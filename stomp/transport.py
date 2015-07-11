import math
import random
import re
import socket
import sys
import threading
import time
import errno
import warnings


##@namespace stomp.transport
# Provides the underlying transport functionality (for stomp message transmission) - (mostly) independent from the actual
# STOMP protocol


from io import BytesIO

try:
    import ssl
    from ssl import SSLError
    DEFAULT_SSL_VERSION = ssl.PROTOCOL_TLSv1
except (ImportError,AttributeError): # python version < 2.6 without the backported ssl module
    ssl = None
    class SSLError:
        pass
    DEFAULT_SSL_VERSION = None

try:
    from socket import SOL_SOCKET, SO_KEEPALIVE
    from socket import SOL_TCP, TCP_KEEPIDLE, TCP_KEEPINTVL, TCP_KEEPCNT
    LINUX_KEEPALIVE_AVAIL=True
except ImportError:
    LINUX_KEEPALIVE_AVAIL=False

import stomp.exception as exception
import stomp.listener as listener
import stomp.utils as utils
from stomp.backward import decode, encode, get_errno, pack

import logging
log = logging.getLogger('stomp.py')

class BaseTransport(listener.Publisher):

    #
    # Used to parse the STOMP "content-length" header lines,
    #
    __content_length_re = re.compile('^content-length[:]\\s*(?P<value>[0-9]+)', re.MULTILINE)

    def __init__(self, wait_on_receipt, auto_decode=True):
        """
        \param wait_on_receipt
            if a receipt is specified, then the send method should wait
            (block) for the server to respond with that receipt-id
            before continuing
        \param auto_decode
            automatically decode message responses as strings, rather than
            leaving them as bytes. This preserves the behaviour as of version 4.0.16.
            (To be defaulted to False as of the next release)
        """
        self.__recvbuf = b''
        self.listeners = {}
        self.running = False
        self.blocking = None
        self.connected = False
        self.connection_error = False
        self.__receipts = {}
        self.__wait_on_receipt = wait_on_receipt

        # flag used when we receive the disconnect receipt
        self.__disconnect_receipt = None

        # function for creating threads used by the connection
        self.create_thread_fc = utils.default_create_thread

        self.__receiver_thread_exit_condition = threading.Condition()
        self.__receiver_thread_exited = False
        self.__send_wait_condition = threading.Condition()
        self.__connect_wait_condition = threading.Condition()
        self.__auto_decode = auto_decode

    def override_threading(self, create_thread_fc):
        """
        Override for thread creation. Use an alternate threading library by
        setting this to a function with a single argument (which is the receiver loop callback).
        The thread which is returned should be started (ready to run)
        """
        self.create_thread_fc = create_thread_fc

    #
    # Manage the connection
    #

    def start(self):
        """
        Start the connection. This should be called after all
        listeners have been registered. If this method is not called,
        no frames will be received by the connection.
        """
        self.running = True
        self.attempt_connection()
        thread = self.create_thread_fc(self.__receiver_loop)
        self.notify('connecting')

    def stop(self):
        """
        Stop the connection. Performs a clean shutdown by waiting for the
        receiver thread to exit.
        """
        self.__receiver_thread_exit_condition.acquire()
        while not self.__receiver_thread_exited:
            self.__receiver_thread_exit_condition.wait()
        self.__receiver_thread_exit_condition.release()

    def is_connected(self):
        return self.connected

    def set_connected(self, connected):
        self.__connect_wait_condition.acquire()
        self.connected = connected
        if connected:
            self.__connect_wait_condition.notify()
        self.__connect_wait_condition.release()

    #
    # Manage objects listening to incoming frames
    #

    def set_listener(self, name, listener):
        """
        Set a named listener to use with this connection

        \see listener::ConnectionListener

        \param name
            the name of the listener
        \param listener
            the listener object
        """
        self.listeners[name] = listener

    def remove_listener(self, name):
        """
        Remove a listener according to the specified name

        \param name the name of the listener to remove
        """
        del self.listeners[name]

    def get_listener(self, name):
        """
        Return the named listener

        \param name the listener to return
        """
        return self.listeners.get(name)

    def process_frame(self, f, frame_str):
        frame_type = f.cmd.lower()
        if frame_type in ['connected', 'message', 'receipt', 'error', 'heartbeat']:
            if frame_type == 'message':
                (f.headers, f.body) = self.notify('before_message', f.headers, f.body)
            self.notify(frame_type, f.headers, f.body)
            if log.isEnabledFor(logging.DEBUG):
                log.debug("Received frame: %r, headers=%r, body=%r", f.cmd, f.headers, f.body)
            else:
                log.info("Received frame: %r, headers=%r, len(body)=%r", f.cmd, f.headers, utils.length(f.body))
        else:
            log.warning("Unknown response frame type: '%s' (frame length was %d)", frame_type, utils.length(frame_str))

    def notify(self, frame_type, headers=None, body=None):
        """
        Utility function for notifying listeners of incoming and outgoing messages

        \param frame_type
            the type of message

        \param headers
            the map of headers associated with the message

        \param body
            the content of the message
        """
        if frame_type == 'receipt':
            # logic for wait-on-receipt notification
            receipt = headers['receipt-id']
            self.__send_wait_condition.acquire()
            try:
                self.__receipts[receipt] = None
                self.__send_wait_condition.notify()
            finally:
                self.__send_wait_condition.release()

            # received a stomp 1.1+ disconnect receipt
            if receipt == self.__disconnect_receipt:
                self.disconnect_socket()

        elif frame_type == 'connected':
            self.set_connected(True)

        elif frame_type == 'disconnected':
            self.set_connected(False)

        rtn = None
        for listener in self.listeners.values():
            if not listener: continue
            if not hasattr(listener, 'on_%s' % frame_type):
                log.debug("listener %s has no method on_%s", listener, frame_type)
                continue

            if frame_type == 'connecting':
                listener.on_connecting(self.current_host_and_port)
                continue
            elif frame_type == 'disconnected':
                listener.on_disconnected()
                continue
            elif frame_type == 'heartbeat':
                listener.on_heartbeat()
                continue

            if frame_type == 'error' and not self.connected:
                self.__connect_wait_condition.acquire()
                self.connection_error = True
                self.__connect_wait_condition.notify()
                self.__connect_wait_condition.release()

            notify_func = getattr(listener, 'on_%s' % frame_type)
            rtn = notify_func(headers, body)
            if rtn:
                (headers, body) = rtn
        if rtn:
            return rtn

    def transmit(self, frame):
        """
        Convert a frame object to a frame string and transmit to the server.
        """
        for listener in self.listeners.values():
            if not listener: continue
            if not hasattr(listener, 'on_send'):
                continue
            listener.on_send(frame)

        lines = utils.convert_frame_to_lines(frame)

        packed_frame = pack(lines)

        if log.isEnabledFor(logging.DEBUG):
            log.debug("Sending frame %s", lines)
        else:
            log.info("Sending frame cmd=%r headers=%r", frame.cmd, frame.headers)

        self.send(encode(packed_frame))

    def send(self, frame):
        pass

    def receive(self):
        pass

    def cleanup(self):
        pass

    def attempt_connection(self):
        pass

    def wait_for_connection(self, timeout=None):
        """
        Wait until we've established a connection with the server.
        """
        if timeout is not None:
            wait_time = timeout / 10.0
        else:
            wait_time = None
        self.__connect_wait_condition.acquire()
        while not self.is_connected() and not self.connection_error:
            self.__connect_wait_condition.wait(wait_time)
        self.__connect_wait_condition.release()

    def __receiver_loop(self):
        """
        Main loop listening for incoming data.
        """
        log.info("Starting receiver loop")
        try:
            while self.running:
                try:
                    while self.running:
                        frames = self.__read()

                        for frame in frames:
                            f = utils.parse_frame(frame)
                            if self.__auto_decode:
                                f.body = decode(f.body)
                            self.process_frame(f, frame)
                except exception.ConnectionClosedException:
                    if self.running:
                        self.notify('disconnected')
                        #
                        # Clear out any half-received messages after losing connection
                        #
                        self.__recvbuf = b''
                        self.running = False
                    break
                finally:
                    self.cleanup()
        finally:
            self.__receiver_thread_exit_condition.acquire()
            self.__receiver_thread_exited = True
            self.__receiver_thread_exit_condition.notifyAll()
            self.__receiver_thread_exit_condition.release()
            log.info("Receiver loop ended")

    def __read(self):
        """
        Read the next frame(s) from the socket.
        """
        fastbuf = BytesIO()
        while self.running:
            try:
                try:
                    c = self.receive()
                except exception.InterruptedException:
                    log.debug("socket read interrupted, restarting")
                    continue
            except Exception:
                _, e, _ = sys.exc_info()
                c = b''
            if len(c) == 0:
                raise exception.ConnectionClosedException()
            fastbuf.write(c)
            if b'\x00' in c:
                break
            elif c == b'\x0a':
                # heartbeat (special case)
                return [c,]
        self.__recvbuf += fastbuf.getvalue()
        fastbuf.close()
        result = []

        if len(self.__recvbuf) > 0 and self.running:
            while True:
                pos = self.__recvbuf.find(b'\x00')

                if pos >= 0:
                    frame = self.__recvbuf[0:pos]
                    preamble_end = frame.find(b'\n\n')
                    if preamble_end >= 0:
                        content_length_match = Transport.__content_length_re.search(decode(frame[0:preamble_end]))
                        if content_length_match:
                            content_length = int(content_length_match.group('value'))
                            content_offset = preamble_end + 2
                            frame_size = content_offset + content_length
                            if frame_size > len(frame):
                                #
                                # Frame contains NUL bytes, need to read more
                                #
                                if frame_size < len(self.__recvbuf):
                                    pos = frame_size
                                    frame = self.__recvbuf[0:pos]
                                else:
                                    #
                                    # Haven't read enough data yet, exit loop and wait for more to arrive
                                    #
                                    break
                    result.append(frame)
                    self.__recvbuf = self.__recvbuf[pos+1:]
                else:
                    break
        return result


class Transport(BaseTransport):
    """
    Represents a STOMP client 'transport'. Effectively this is the communications mechanism without the definition of the protocol.
    """

    def __init__(self,
                 host_and_ports=None,
                 prefer_localhost=True,
                 try_loopback_connect=True,
                 reconnect_sleep_initial=0.1,
                 reconnect_sleep_increase=0.5,
                 reconnect_sleep_jitter=0.1,
                 reconnect_sleep_max=60.0,
                 reconnect_attempts_max=3,
                 use_ssl=False,
                 ssl_key_file=None,
                 ssl_cert_file=None,
                 ssl_ca_certs=None,
                 ssl_cert_validator=None,
                 wait_on_receipt=False,
                 ssl_version=None,
                 timeout=None,
                 keepalive=None,
                 vhost=None,
                 auto_decode=True
                 ):
        """
        \param host_and_ports
            a list of (host, port) tuples.

        \param prefer_localhost
            if True and the local host is mentioned in the (host,
            port) tuples, try to connect to this first

        \param try_loopback_connect
            if True and the local host is found in the host
            tuples, try connecting to it using loopback interface
            (127.0.0.1)

        \param reconnect_sleep_initial
            initial delay in seconds to wait before reattempting
            to establish a connection if connection to any of the
            hosts fails.

        \param reconnect_sleep_increase
            factor by which the sleep delay is increased after
            each connection attempt. For example, 0.5 means
            to wait 50% longer than before the previous attempt,
            1.0 means wait twice as long, and 0.0 means keep
            the delay constant.

        \param reconnect_sleep_max
            maximum delay between connection attempts, regardless
            of the reconnect_sleep_increase.

        \param reconnect_sleep_jitter
            random additional time to wait (as a percentage of
            the time determined using the previous parameters)
            between connection attempts in order to avoid
            stampeding. For example, a value of 0.1 means to wait
            an extra 0%-10% (randomly determined) of the delay
            calculated using the previous three parameters.

        \param reconnect_attempts_max
            maximum attempts to reconnect

        \param use_ssl
            deprecated, see Transport::set_ssl

        \param ssl_cert_file
            deprecated, see Transport::set_ssl

        \param ssl_key_file
            deprecated, see Transport::set_ssl

        \param ssl_ca_certs
            deprecated, see Transport::set_ssl

        \param ssl_cert_validator
            deprecated, see Transport::set_ssl

        \param ssl_version
            deprecated, see Transport::set_ssl

        \param timeout
            the timeout value to use when connecting the stomp socket

        \param keepalive
            some operating systems support sending the occasional heart
            beat packets to detect when a connection fails.  This
            parameter can either be set set to a boolean to turn on the
            default keepalive options for your OS, or as a tuple of
            values, which also enables keepalive packets, but specifies
            options specific to your OS implementation

        \param vhost
            specify a virtual hostname to provide in the 'host' header of the connection
        """

        BaseTransport.__init__(self, wait_on_receipt, auto_decode)

        if host_and_ports is None:
            host_and_ports = [('localhost', 61613)]

        sorted_host_and_ports = []
        sorted_host_and_ports.extend(host_and_ports)

        #
        # If localhost is preferred, make sure all (host, port) tuples that refer to the local host come first in the list
        #
        if prefer_localhost:
            sorted_host_and_ports.sort(key=utils.is_localhost)

        #
        # If the user wishes to attempt connecting to local ports using the loopback interface, for each (host, port) tuple
        # referring to a local host, add an entry with the host name replaced by 127.0.0.1 if it doesn't exist already
        #
        loopback_host_and_ports = []
        if try_loopback_connect:
            for host_and_port in sorted_host_and_ports:
                if utils.is_localhost(host_and_port) == 1:
                    port = host_and_port[1]
                    if (not ("127.0.0.1", port) in sorted_host_and_ports
                        and not ("localhost", port) in sorted_host_and_ports):
                        loopback_host_and_ports.append(("127.0.0.1", port))

        #
        # Assemble the final, possibly sorted list of (host, port) tuples
        #
        self.__host_and_ports = []
        self.__host_and_ports.extend(loopback_host_and_ports)
        self.__host_and_ports.extend(sorted_host_and_ports)

        self.__reconnect_sleep_initial = reconnect_sleep_initial
        self.__reconnect_sleep_increase = reconnect_sleep_increase
        self.__reconnect_sleep_jitter = reconnect_sleep_jitter
        self.__reconnect_sleep_max = reconnect_sleep_max
        self.__reconnect_attempts_max = reconnect_attempts_max
        self.__timeout = timeout

        self.socket = None
        self.__socket_semaphore = threading.BoundedSemaphore(1)
        self.current_host_and_port = None

        # setup SSL
        self.__ssl_params = {}
        if use_ssl:
            warnings.warn("Deprecated: use set_ssl instead", DeprecationWarning)
            self.set_ssl(host_and_ports,
                         ssl_key_file,
                         ssl_cert_file,
                         ssl_ca_certs,
                         ssl_cert_validator,
                         ssl_version)

        self.__keepalive = keepalive
        self.vhost = vhost

    def is_connected(self):
        """
        Return true if the socket managed by this connection is connected
        """
        try:
            return self.socket is not None and self.socket.getsockname()[1] != 0 and BaseTransport.is_connected(self)
        except socket.error:
            return False

    def disconnect_socket(self):
        """
        Disconnect the underlying socket connection
        """
        self.running = False
        if self.socket is not None:
            if self.__need_ssl():
                #
                # Even though we don't want to use the socket, unwrap is the only API method which does a proper SSL
                # shutdown
                #
                try:
                    self.socket = self.socket.unwrap()
                except Exception:
                    #
                    # unwrap seems flaky on Win with the back-ported ssl mod, so catch any exception and log it
                    #
                    _, e, _ = sys.exc_info()
                    log.warn(e)
            elif hasattr(socket, 'SHUT_RDWR'):
                try:
                    self.socket.shutdown(socket.SHUT_RDWR)
                except socket.error:
                    _, e, _ = sys.exc_info()
                    # ignore when socket already closed
                    if get_errno(e) != errno.ENOTCONN:
                        log.warn("Unable to issue SHUT_RDWR on socket because of error '%s'", e)

        #
        # split this into a separate check, because sometimes the socket is nulled between shutdown and this call
        #
        if self.socket is not None:
            try:
                self.socket.close()
            except socket.error:
                _, e, _ = sys.exc_info()
                log.warn("Unable to close socket because of error '%s'", e)
        self.current_host_and_port = None


    def send(self, encoded_frame):
        if self.socket is not None:
            try:
                self.__socket_semaphore.acquire()
                try:
                    self.socket.sendall(encoded_frame)
                finally:
                    self.__socket_semaphore.release()
            except Exception:
                _, e, _ = sys.exc_info()
                log.error("Error sending frame", exc_info=1)
                raise e
        else:
            raise exception.NotConnectedException()


    def receive(self):
        try:
            return self.socket.recv(1024)
        except socket.error:
            _, e, _ = sys.exc_info()
            if get_errno(e) in (errno.EAGAIN, errno.EINTR):
                log.debug("socket read interrupted, restarting")
                raise exception.InterruptedException()
            raise


    def cleanup(self):
        try:
            self.socket.close()
        except:
            pass # ignore errors when attempting to close socket
        self.socket = None
        self.current_host_and_port = None


    def __enable_keepalive(self):
        def try_setsockopt(sock, name, fam, opt, val):
            if val is None:
                return True  # no value to set always works
            try:
                sock.setsockopt(fam, opt, val)
                log.info("keepalive: set %r option to %r on socket", name, val)
            except:
                log.error("keepalive: unable to set %r option to %r on socket", name, val)
                return False
            return True

        ka = self.__keepalive

        if not ka:
            return

        if ka:
            ka_sig = 'auto'
            ka_args = ()
        else:
            try:
                ka_sig = ka[0]
                ka_args = ka[1:]
            except Exception:
                log.error("keepalive: bad specification %r", ka)
                return

        if ka_sig == 'auto':
            if LINUX_KEEPALIVE_AVAIL:
                ka_sig = 'linux'
                ka_args = None
                log.info("keepalive: autodetected linux-style support")
            else:
                log.error("keepalive: unable to detect any implementation, DISABLED!")
                return

        if ka_sig == 'linux':
            log.info("keepalive: activating linux-style support")
            if ka_args is None:
                log.info("keepalive: using system defaults")
                ka_args = (None, None, None)
            lka_idle, lka_intvl, lka_cnt = ka_args
            if try_setsockopt(self.socket, 'enable', SOL_SOCKET, SO_KEEPALIVE, 1):
                try_setsockopt(self.socket, 'idle time', SOL_TCP, TCP_KEEPIDLE, lka_idle)
                try_setsockopt(self.socket, 'interval', SOL_TCP, TCP_KEEPINTVL, lka_intvl)
                try_setsockopt(self.socket, 'count', SOL_TCP, TCP_KEEPCNT, lka_cnt)
        else:
            log.error("keepalive: implementation %r not recognized or not supported", ka_sig)

    def attempt_connection(self):
        """
        Try connecting to the (host, port) tuples specified at construction time.
        """
        self.connection_error = False
        sleep_exp = 1
        connect_count = 0

        while self.running and self.socket is None and connect_count < self.__reconnect_attempts_max:
            for host_and_port in self.__host_and_ports:
                try:
                    log.info("Attempting connection to host %s, port %s", host_and_port[0], host_and_port[1])
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.__enable_keepalive()
                    need_ssl = self.__need_ssl(host_and_port)

                    if need_ssl:  # wrap socket
                        ssl_params = self.get_ssl(host_and_port)
                        if ssl_params['ca_certs']:
                            cert_validation = ssl.CERT_REQUIRED
                        else:
                            cert_validation = ssl.CERT_NONE
                        self.socket = ssl.wrap_socket(
                            self.socket,
                            keyfile=ssl_params['key_file'],
                            certfile=ssl_params['cert_file'],
                            cert_reqs=cert_validation,
                            ca_certs=ssl_params['ca_certs'],
                            ssl_version=ssl_params['ssl_version'])
                        self.socket.settimeout(self.__timeout)

                    if self.blocking is not None:
                        self.socket.setblocking(self.blocking)
                    self.socket.connect(host_and_port)

                    #
                    # Validate server cert
                    #
                    if need_ssl and ssl_params['cert_validator']:
                        cert = self.socket.getpeercert()
                        (ok, errmsg) = ssl_params['cert_validator'](cert, host_and_port[0])
                        if not ok:
                            raise SSLError("Server certificate validation failed: %s", errmsg)

                    self.current_host_and_port = host_and_port
                    log.info("Established connection to host %s, port %s", host_and_port[0], host_and_port[1])
                    break
                except socket.error:
                    self.socket = None
                    connect_count += 1
                    log.warning("Could not connect to host %s, port %s", host_and_port[0], host_and_port[1], exc_info=1)

            if self.socket is None:
                sleep_duration = (min(self.__reconnect_sleep_max,
                                      ((self.__reconnect_sleep_initial / (1.0 + self.__reconnect_sleep_increase))
                                       * math.pow(1.0 + self.__reconnect_sleep_increase, sleep_exp)))
                                  * (1.0 + random.random() * self.__reconnect_sleep_jitter))
                sleep_end = time.time() + sleep_duration
                log.debug("Sleeping for %.1f seconds before attempting reconnect", sleep_duration)
                while self.running and time.time() < sleep_end:
                    time.sleep(0.2)

                if sleep_duration < self.__reconnect_sleep_max:
                    sleep_exp += 1

        if not self.socket:
            raise exception.ConnectFailedException()


    def set_ssl(self,
                for_hosts=[],
                key_file=None,
                cert_file=None,
                ca_certs=None,
                cert_validator=None,
                ssl_version=DEFAULT_SSL_VERSION):
        """
        Sets up SSL configuration for the given hosts.

        This ensures socket is wrapped in a SSL connection, raising an
        exception if the SSL module can't be found.

        \param for_hosts
            hosts this SSL configuration should be applied to

        \param cert_file
            the path to a X509 certificate

        \param key_file
            the path to a X509 key file

        \param ca_certs
            the path to the a file containing CA certificates
            to validate the server against.  If this is not set,
            server side certificate validation is not done.

        \param cert_validator
            function which performs extra validation on the client
            certificate, for example checking the returned
            certificate has a commonName attribute equal to the
            hostname (to avoid man in the middle attacks).
            The signature is:
                (OK, err_msg) = validation_function(cert, hostname)
            where OK is a boolean, and cert is a certificate structure
            as returned by ssl.SSLSocket.getpeercert()

        \param ssl_version
            SSL protocol to use for the connection. This should be
            one of the PROTOCOL_x constants provided by the ssl module.
            The default is ssl.PROTOCOL_TLSv1
        """
        if not ssl:
            raise Exception("SSL connection requested, but SSL library not found")

        for host_port in for_hosts:
            self.__ssl_params[host_port] = dict(key_file=key_file,
                                                cert_file=cert_file,
                                                ca_certs=ca_certs,
                                                cert_validator=cert_validator,
                                                ssl_version=ssl_version)


    def __need_ssl(self, host_and_port=None):
        """
        Whether current host needs SSL or not.
        """
        if not host_and_port:
            host_and_port = self.current_host_and_port

        return host_and_port in self.__ssl_params


    def get_ssl(self, host_and_port=None):
        """
        Get SSL params for the given host.

        \param host_and_port
            The host/port pair we want SSL params for, default current_host_port
        """
        if not host_and_port:
            host_and_port = self.current_host_and_port

        return self.__ssl_params.get(host_and_port)
