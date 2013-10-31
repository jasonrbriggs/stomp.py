import math
import random
import re
import socket
import sys
import threading
import time
import types
import xml.dom.minidom
import errno


##@namespace stomp.transport
# Provides the underlying transport functionality (for stomp message transmission) - (mostly) independent from the actual 
# STOMP protocol


try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

try:
    import ssl
    from ssl import SSLError
    DEFAULT_SSL_VERSION = ssl.PROTOCOL_SSLv3
except ImportError: # python version < 2.6 without the backported ssl module
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

import exception
import listener
import utils
from backward import decode, encode, pack, NULL

try:
    import uuid    
except ImportError:
    from backward import uuid

import logging
log = logging.getLogger('stomp.py')

class Transport(object):
    """
    Represents a STOMP client 'transport'. Effectively this is the communications mechanism without the definition of the protocol.
    """
    
    #
    # Used to parse the STOMP "content-length" header lines,
    #
    __content_length_re = re.compile('^content-length[:]\\s*(?P<value>[0-9]+)', re.MULTILINE)

    def __init__(self, 
                 host_and_ports = [ ('localhost', 61613) ], 
                 prefer_localhost = True,
                 try_loopback_connect = True,
                 reconnect_sleep_initial = 0.1,
                 reconnect_sleep_increase = 0.5,
                 reconnect_sleep_jitter = 0.1,
                 reconnect_sleep_max = 60.0,
                 reconnect_attempts_max = 3,
                 use_ssl = False,
                 ssl_key_file = None,
                 ssl_cert_file = None,
                 ssl_ca_certs = None,
                 ssl_cert_validator = None,
                 wait_on_receipt = False,
                 ssl_version = DEFAULT_SSL_VERSION,
                 timeout = None,
                 keepalive = None,
                 vhost = None
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
            connect using SSL to the socket.  This wraps the 
            socket in a SSL connection.  The constructor will 
            raise an exception if you ask for SSL, but it can't
            find the SSL module.

        \param ssl_cert_file
            the path to a X509 certificate 

        \param ssl_key_file
            the path to a X509 key file

        \param ssl_ca_certs
            the path to the a file containing CA certificates
            to validate the server against.  If this is not set,
            server side certificate validation is not done. 

        \param ssl_cert_validator
            function which performs extra validation on the client
            certificate, for example checking the returned
            certificate has a commonName attribute equal to the
            hostname (to avoid man in the middle attacks).
            The signature is:
                (OK, err_msg) = validation_function(cert, hostname)
            where OK is a boolean, and cert is a certificate structure
            as returned by ssl.SSLSocket.getpeercert()
            
        \param wait_on_receipt
            if a receipt is specified, then the send method should wait
            (block) for the server to respond with that receipt-id
            before continuing
            
        \param ssl_version
            SSL protocol to use for the connection. This should be
            one of the PROTOCOL_x constants provided by the ssl module.
            The default is ssl.PROTOCOL_SSLv3
            
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

        sorted_host_and_ports = []
        sorted_host_and_ports.extend(host_and_ports)

        #
        # If localhost is preferred, make sure all (host, port) tuples that refer to the local host come first in the list
        #
        if prefer_localhost:
            sorted_host_and_ports.sort(key = utils.is_localhost)

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

        self.__recvbuf = ''

        self.listeners = {}

        self.__reconnect_sleep_initial = reconnect_sleep_initial
        self.__reconnect_sleep_increase = reconnect_sleep_increase
        self.__reconnect_sleep_jitter = reconnect_sleep_jitter
        self.__reconnect_sleep_max = reconnect_sleep_max
        self.__reconnect_attempts_max = reconnect_attempts_max
        self.__timeout = timeout
        
        self.__socket = None
        self.__socket_semaphore = threading.BoundedSemaphore(1)
        self.current_host_and_port = None

        self.__receiver_thread_exit_condition = threading.Condition()
        self.__receiver_thread_exited = False
        self.__send_wait_condition = threading.Condition()
        self.__connect_wait_condition = threading.Condition()
        
        self.blocking = None
        self.connected = False
        
        # setup SSL
        if use_ssl and not ssl:
            raise Exception("SSL connection requested, but SSL library not found.")
        self.__ssl = use_ssl
        self.__ssl_cert_file = ssl_cert_file
        self.__ssl_key_file = ssl_key_file
        self.__ssl_ca_certs = ssl_ca_certs
        self.__ssl_cert_validator = ssl_cert_validator
        self.__ssl_version = ssl_version
        
        self.__receipts = {}
        self.__wait_on_receipt = wait_on_receipt
        
        # flag used when we receive the disconnect receipt
        self.__disconnect_receipt = None
        
        # function for creating threads used by the connection
        self.create_thread_fc = utils.default_create_thread

        self.__keepalive = keepalive
        self.vhost = vhost

            
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
        self.__attempt_connection()
        thread = self.create_thread_fc(self.__receiver_loop)
        self.__notify('connecting')

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
        """
        Return true if the socket managed by this connection is connected
        """
        try:
            return self.__socket is not None and self.__socket.getsockname()[1] != 0 and self.connected
        except socket.error:
            return False
            
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
        if name in self.listeners:
            return self.listeners[name]
        else:
            return None
        
    def disconnect_socket(self):
        """
        Disconnect the underlying socket connection
        """
        self.running = False
        if self.__socket is not None:
            if self.__ssl:
                #
                # Even though we don't want to use the socket, unwrap is the only API method which does a proper SSL shutdown
                #
                try:
                    self.__socket = self.__socket.unwrap()
                except Exception:
                    #
                    # unwrap seems flaky on Win with the backported ssl mod, so catch any exception and log it
                    #
                    _, e, _ = sys.exc_info()
                    log.warn(e)
            elif hasattr(socket, 'SHUT_RDWR'):
                try:
                    self.__socket.shutdown(socket.SHUT_RDWR)
                except socket.error:
                    _, e, _ = sys.exc_info()
                    log.warn('Unable to issue SHUT_RDWR on socket because of error "%s"' % e)

        #
        # split this into a separate check, because sometimes the socket is nulled between shutdown and this call
        #
        if self.__socket is not None:
            try:
                self.__socket.close()
            except socket.error:
                _, e, _ = sys.exc_info()
                log.warn('Unable to close socket because of error "%s"' % e)
        self.current_host_and_port = None

    def send_frame(self, frame):
        """
        Convert a frame object to a frame string and transmit to the server.
        """
        for listener in self.listeners.values():
            if not listener: continue
            if not hasattr(listener, 'on_send'):
                continue
            listener.on_send(frame)

        lines = [ ]
        if frame.cmd:
            lines.append(frame.cmd)
            lines.append("\n")
        for key, vals in sorted(frame.headers.items()):
            if type(vals) != tuple:
                vals = ( vals, )
            for val in vals:
                lines.append('%s:%s\n' % (key, val))
        lines.append('\n')
        if frame.body:
            lines.append(frame.body)

        if frame.cmd:
            lines.append(NULL)

        packed_frame = pack(lines)

        log.info("Sending frame %s" % lines)

        if self.__socket is not None:
            try:
                self.__socket_semaphore.acquire()
                try:
                    self.__socket.sendall(encode(packed_frame))
                finally:
                    self.__socket_semaphore.release()
            except Exception:
                _, e, _ = sys.exc_info()
                log.error("Error sending frame: %s" % e)
                raise e
        else:
            raise exception.NotConnectedException()

    def __notify(self, frame_type, headers=None, body=None):
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
            
            # received a stomp 1.1 disconnect receipt
            if receipt == self.__disconnect_receipt:
                self.disconnect_socket()

        elif frame_type == 'connected':
            self.set_connected(True)

        elif frame_type == 'disconnected':
            self.set_connected(False)

        for listener in self.listeners.values():
            if not listener: continue
            if not hasattr(listener, 'on_%s' % frame_type):
                log.debug('listener %s has no method on_%s' % (listener, frame_type))
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

            notify_func = getattr(listener, 'on_%s' % frame_type)
            rtn = notify_func(headers, body)
            if rtn:
                return rtn

    def __receiver_loop(self):
        """
        Main loop listening for incoming data.
        """
        log.debug("Starting receiver loop")
        try:
            try:
                while self.running:
                    if self.__socket is None:
                        break

                    try:
                        try:
                            while self.running:
                                frames = self.__read()
                                
                                for frame in frames:
                                    f = utils.parse_frame(frame)
                                    log.debug("Received frame: %r, headers=%r, body=%r" % (f.cmd, f.headers, f.body))
                                    frame_type = f.cmd.lower()
                                    if frame_type in [ 'connected', 'message', 'receipt', 'error', 'heartbeat' ]:
                                        if frame_type == 'message':
                                            (f.headers, f.body) = self.__notify('before_message', f.headers, f.body)
                                        self.__notify(frame_type, f.headers, f.body)
                                    else:
                                        log.warning('Unknown response frame type: "%s" (frame length was %d)' % (frame_type, len(frame)))
                        finally:
                            try:
                                self.__socket.close()
                            except:
                                pass # ignore errors when attempting to close socket
                            self.__socket = None
                            self.current_host_and_port = None
                    except exception.ConnectionClosedException:
                        if self.running:
                            log.error("Lost connection")
                            self.__notify('disconnected')
                            #
                            # Clear out any half-received messages after losing connection
                            #
                            self.__recvbuf = ''
                            self.running = False
                        break
            except:
                log.exception("An unhandled exception was encountered in the stomp receiver loop")

        finally:
            self.__receiver_thread_exit_condition.acquire()
            self.__receiver_thread_exited = True
            self.__receiver_thread_exit_condition.notifyAll()
            self.__receiver_thread_exit_condition.release()
            log.debug("Receiver loop ended")            

    def __read(self):
        """
        Read the next frame(s) from the socket.
        """
        fastbuf = StringIO()
        while self.running:
            try:
                try:
                    c = self.__socket.recv(1024)
                except socket.error:
                    _, e, _ = sys.exc_info()
                    if e.args[0] in (errno.EAGAIN, errno.EINTR):
                        log.debug("socket read interrupted, restarting")
                        continue
                    raise
                c = decode(c)
            except Exception:
                _, e, _ = sys.exc_info()
                c = ''
            if len(c) == 0:
                raise exception.ConnectionClosedException()
            fastbuf.write(c)
            if '\x00' in c:
                break
            elif c == '\x0a':
                # heartbeat (special case)
                return c
        self.__recvbuf += fastbuf.getvalue()
        fastbuf.close()
        result = []

        if len(self.__recvbuf) > 0 and self.running:
            while True:
                pos = self.__recvbuf.find('\x00')

                if pos >= 0:
                    frame = self.__recvbuf[0:pos]
                    preamble_end = frame.find('\n\n')
                    if preamble_end >= 0:
                        content_length_match = Transport.__content_length_re.search(frame[0:preamble_end])
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

    def __enable_keepalive(self):
        def try_setsockopt(sock, name, fam, opt, val):
            if val is None:
                return True # no value to set always works
            try:
                sock.setsockopt(fam, opt, val)
                log.debug('keepalive: set %r option to %r on socket' % (name, val))
            except:
                log.error('keepalive: unable to set %r option to %r on socket' % (name,val))
                return False
            return True

        ka = self.__keepalive

        if not ka:
            return

        if ka == True:
            ka_sig = 'auto'
            ka_args = ()
        else:
            try:
                ka_sig = ka[0]
                ka_args = ka[1:]
            except Exception:
                log.error('keepalive: bad specification %r' % (ka,))
                return

        if ka_sig == 'auto':
            if LINUX_KEEPALIVE_AVAIL:
                ka_sig = 'linux'
                ka_args = None
                log.debug('keepalive: autodetected linux-style support')
            else:
                log.error('keepalive: unable to detect any implementation, DISABLED!')
                return

        if ka_sig == 'linux':
            log.debug('keepalive: activating linux-style support')
            if ka_args is None:
                log.debug('keepalive: using system defaults')
                ka_args = (None, None, None)
            lka_idle, lka_intvl, lka_cnt = ka_args
            if try_setsockopt(self.__socket, 'enable', SOL_SOCKET, SO_KEEPALIVE, 1):
                try_setsockopt(self.__socket, 'idle time', SOL_TCP, TCP_KEEPIDLE, lka_idle)
                try_setsockopt(self.__socket, 'interval', SOL_TCP, TCP_KEEPINTVL, lka_intvl)
                try_setsockopt(self.__socket, 'count', SOL_TCP, TCP_KEEPCNT, lka_cnt)
        else:
            log.error('keepalive: implementation %r not recognized or not supported' % ka_sig)

    def __attempt_connection(self):
        """
        Try connecting to the (host, port) tuples specified at construction time.
        """
        sleep_exp = 1
        connect_count = 0
        while self.running and self.__socket is None and connect_count < self.__reconnect_attempts_max:
            for host_and_port in self.__host_and_ports:
                try:
                    log.debug("Attempting connection to host %s, port %s" % host_and_port)
                    self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.__enable_keepalive()

                    if self.__ssl: # wrap socket
                        if self.__ssl_ca_certs:
                            cert_validation = ssl.CERT_REQUIRED
                        else:
                            cert_validation = ssl.CERT_NONE
                        self.__socket = ssl.wrap_socket(self.__socket, keyfile = self.__ssl_key_file,
                                certfile = self.__ssl_cert_file, cert_reqs = cert_validation, 
                                ca_certs = self.__ssl_ca_certs, ssl_version = self.__ssl_version)
                    self.__socket.settimeout(self.__timeout)
                    if self.blocking is not None:
                        self.__socket.setblocking(self.blocking)
                    self.__socket.connect(host_and_port)
                    
                    #
                    # Validate server cert
                    #
                    if self.__ssl and self.__ssl_cert_validator: 
                        cert = self.__socket.getpeercert()
                        (ok, errmsg) = apply(self.__ssl_cert_validator, (cert, host_and_port[0]))
                        if not ok:
                            raise SSLError("Server certificate validation failed: %s" % errmsg)

                    self.current_host_and_port = host_and_port
                    log.info("Established connection to host %s, port %s" % host_and_port)
                    break
                except socket.error:
                    self.__socket = None
                    if isinstance(sys.exc_info()[1], tuple):
                        exc = sys.exc_info()[1][1]
                    else:
                        exc = sys.exc_info()[1]
                    connect_count += 1
                    log.warning("Could not connect to host %s, port %s: %s" % (host_and_port[0], host_and_port[1], exc))

            if self.__socket is None:
                sleep_duration = (min(self.__reconnect_sleep_max, 
                                      ((self.__reconnect_sleep_initial / (1.0 + self.__reconnect_sleep_increase)) 
                                       * math.pow(1.0 + self.__reconnect_sleep_increase, sleep_exp)))
                                  * (1.0 + random.random() * self.__reconnect_sleep_jitter))
                sleep_end = time.time() + sleep_duration
                log.debug("Sleeping for %.1f seconds before attempting reconnect" % sleep_duration)
                while self.running and time.time() < sleep_end:
                    time.sleep(0.2)

                if sleep_duration < self.__reconnect_sleep_max:
                    sleep_exp += 1

        if not self.__socket:
            raise exception.ConnectFailedException()

    def wait_for_connection(self):
        """
        Wait until we've established a connection with the server.
        """
        self.__connect_wait_condition.acquire()
        while not self.is_connected(): 
            self.__connect_wait_condition.wait()
        self.__connect_wait_condition.release()
