import errno
import math
import random
import sys
import time
from time import monotonic
import websocket

try:
    from socket import SOL_SOCKET, SO_KEEPALIVE, SOL_TCP, TCP_KEEPIDLE, TCP_KEEPINTVL, TCP_KEEPCNT
    LINUX_KEEPALIVE_AVAIL = True
except ImportError:
    LINUX_KEEPALIVE_AVAIL = False

try:
    import ssl
    from ssl import SSLError
    DEFAULT_SSL_VERSION = ssl.PROTOCOL_TLS_CLIENT
except (ImportError, AttributeError):
    ssl = None
    class SSLError(object):
        pass
    DEFAULT_SSL_VERSION = None

try:
    from socket import IPPROTO_TCP
    MAC_KEEPALIVE_AVAIL = True
except ImportError:
    MAC_KEEPALIVE_AVAIL = False

from stomp.transport import BaseTransport, DEFAULT_SSL_VERSION
from stomp.utils import *
from stomp.connect import BaseConnection, StompConnection12
from stomp.protocol import Protocol12
from stomp.exception import *
from stomp import logging


class WSTransport(BaseTransport):
    """
    Represents a STOMP client websocket 'transport'. Effectively this is the communications mechanism without the definition of
    the protocol.

    :param list((str,int)) host_and_ports: a list of (host, port) tuples
    :param bool prefer_localhost: if True and the local host is mentioned in the (host,
        port) tuples, try to connect to this first
    :param bool try_loopback_connect: if True and the local host is found in the host
        tuples, try connecting to it using loopback interface
        (127.0.0.1)
    :param float reconnect_sleep_initial: initial delay in seconds to wait before reattempting
        to establish a connection if connection to any of the
        hosts fails.
    :param float reconnect_sleep_increase: factor by which the sleep delay is increased after
        each connection attempt. For example, 0.5 means
        to wait 50% longer than before the previous attempt,
        1.0 means wait twice as long, and 0.0 means keep
        the delay constant.
    :param float reconnect_sleep_max: maximum delay between connection attempts, regardless
        of the reconnect_sleep_increase.
    :param float reconnect_sleep_jitter: random additional time to wait (as a percentage of
        the time determined using the previous parameters)
        between connection attempts in order to avoid
        stampeding. For example, a value of 0.1 means to wait
        an extra 0%-10% (randomly determined) of the delay
        calculated using the previous three parameters.
    :param int reconnect_attempts_max: maximum attempts to reconnect (Can also be used for infinite attempts : `-1`)
    :param timeout: the timeout value to use when connecting the stomp socket
    :param keepalive: some operating systems support sending the occasional heart
        beat packets to detect when a connection fails.  This
        parameter can either be set set to a boolean to turn on the
        default keepalive options for your OS, or as a tuple of
        values, which also enables keepalive packets, but specifies
        options specific to your OS implementation.
        For linux, supply ("linux", ka_idle, ka_intvl, ka_cnt)
        For macos, supply ("mac", ka_intvl)
    :param str vhost: specify a virtual hostname to provide in the 'host' header of the connection
    :param int recv_bytes: the number of bytes to use when calling recv
    :param bool binary_mode: if true, then send binary data frames (opcode 0x2) rather than text data frames (opcode 0x1)
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
                 timeout=None,
                 keepalive=None,
                 vhost=None,
                 auto_decode=True,
                 encoding="utf-8",
                 recv_bytes=1024,
                 is_eol_fc=is_eol_default,
                 bind_host_port=None,
                 ws_path=None,
                 header=None,
                 binary_mode=False):
        BaseTransport.__init__(self, auto_decode, encoding, is_eol_fc)

        if host_and_ports is None:
            logging.debug("no hosts_and_ports specified, adding default localhost")
            host_and_ports = [("localhost", 61613)]

        sorted_host_and_ports = []
        sorted_host_and_ports.extend(host_and_ports)

        #
        # If localhost is preferred, make sure all (host, port) tuples that refer to the local host come first in
        # the list
        #
        if prefer_localhost:
            sorted_host_and_ports.sort(key=is_localhost)

        #
        # If the user wishes to attempt connecting to local ports using the loopback interface, for each (host, port)
        # tuple referring to a local host, add an entry with the host name replaced by 127.0.0.1 if it doesn't
        # exist already
        #
        loopback_host_and_ports = []
        if try_loopback_connect:
            for host_and_port in sorted_host_and_ports:
                if is_localhost(host_and_port) == 1:
                    port = host_and_port[1]
                    if not (("127.0.0.1", port) in sorted_host_and_ports or (
                    "localhost", port) in sorted_host_and_ports):
                        loopback_host_and_ports.append(("127.0.0.1", port))

        #
        # Assemble the final, possibly sorted list of (host, port) tuples
        #
        self.__host_and_ports = []
        self.__host_and_ports.extend(loopback_host_and_ports)
        self.__host_and_ports.extend(sorted_host_and_ports)
        self.__bind_host_port = bind_host_port

        self.__reconnect_sleep_initial = reconnect_sleep_initial
        self.__reconnect_sleep_increase = reconnect_sleep_increase
        self.__reconnect_sleep_jitter = reconnect_sleep_jitter
        self.__reconnect_sleep_max = reconnect_sleep_max
        self.__reconnect_attempts_max = reconnect_attempts_max
        self.__timeout = timeout
        self.__binary_mode = binary_mode

        self.socket = None
        self.__socket_semaphore = threading.BoundedSemaphore(1)
        self.current_host_and_port = None
        self.vhost = vhost
        self.ws_path = ws_path
        self.header = header

        # setup SSL
        self.__ssl_params = {}
        self.__keepalive = keepalive
        self.__recv_bytes = recv_bytes

    def is_connected(self):
        """
        Return true if the socket managed by this connection is connected

        :rtype: bool
        """
        try:
            return self.socket is not None and self.socket.getstatus() == 101 and BaseTransport.is_connected(self)
        except socket.error:
            return False

    def disconnect_socket(self):
        """
        Disconnect the underlying socket connection
        """
        self.running = False
        if self.socket is not None:
            try:
                self.socket.shutdown()
            except socket.error:
                _, e, _ = sys.exc_info()
                # ignore when socket already closed
                if get_errno(e) != errno.ENOTCONN:
                    logging.warning("Unable to issue SHUT_RDWR on socket because of error '%s'", e)

        #
        # split this into a separate check, because sometimes the socket is nulled between shutdown and this call
        #
        if self.socket is not None:
            try:
                self.socket.close()
            except socket.error:
                _, e, _ = sys.exc_info()
                logging.warning("unable to close socket because of error '%s'", e)
        self.current_host_and_port = None
        self.socket = None
        if not self.notified_on_disconnect:
            self.notify("disconnected")

    def send(self, encoded_frame):
        """
        :param bytes encoded_frame:
        """
        if self.socket is not None:
            try:
                with self.__socket_semaphore:
                    if self.__binary_mode:
                        opcode = websocket.ABNF.OPCODE_BINARY
                    else:
                        opcode = websocket.ABNF.OPCODE_TEXT

                    self.socket.send(encoded_frame, opcode)
            except Exception:
                _, e, _ = sys.exc_info()
                logging.error("error sending frame", exc_info=True)
                raise e
        else:
            raise NotConnectedException()

    def receive(self):
        """
        :rtype: bytes
        """
        try:
            opcode, data = self.socket.recv_data()
            return data
        except socket.error:
            _, e, _ = sys.exc_info()
            if get_errno(e) in (errno.EAGAIN, errno.EINTR):
                logging.debug("socket read interrupted, restarting")
                raise InterruptedException()
            if self.is_connected():
                raise

    def cleanup(self):
        """
        Close the socket and clear the current host and port details.
        """
        try:
            self.socket.close()
        except:
            pass  # ignore errors when attempting to close socket
        self.socket = None

    def __enable_keepalive(self):
        def try_setsockopt(sock, name, fam, opt, val):
            if val is None:
                return True  # no value to set always works
            try:
                sock.setsockopt(fam, opt, val)
                logging.info("keepalive: set %r option to %r on socket", name, val)
            except:
                logging.error("keepalive: unable to set %r option to %r on socket", name, val)
                return False
            return True

        ka = self.__keepalive

        if not ka:
            return

        if ka is True:
            ka_sig = "auto"
            ka_args = ()
        else:
            try:
                ka_sig = ka[0]
                ka_args = ka[1:]
            except Exception:
                logging.error("keepalive: bad specification %r", ka)
                return

        if ka_sig == "auto":
            if LINUX_KEEPALIVE_AVAIL:
                ka_sig = "linux"
                ka_args = None
                logging.info("keepalive: autodetected linux-style support")
            elif MAC_KEEPALIVE_AVAIL:
                ka_sig = "mac"
                ka_args = None
                logging.info("keepalive: autodetected mac-style support")
            else:
                logging.error("keepalive: unable to detect any implementation, DISABLED!")
                return

        if ka_sig == "linux":
            logging.info("keepalive: activating linux-style support")
            if ka_args is None:
                logging.info("keepalive: using system defaults")
                ka_args = (None, None, None)
            ka_idle, ka_intvl, ka_cnt = ka_args
            if try_setsockopt(self.socket, "enable", SOL_SOCKET, SO_KEEPALIVE, 1):
                try_setsockopt(self.socket, "idle time", SOL_TCP, TCP_KEEPIDLE, ka_idle)
                try_setsockopt(self.socket, "interval", SOL_TCP, TCP_KEEPINTVL, ka_intvl)
                try_setsockopt(self.socket, "count", SOL_TCP, TCP_KEEPCNT, ka_cnt)
        elif ka_sig == "mac":
            logging.info("keepalive: activating mac-style support")
            if ka_args is None:
                logging.info("keepalive: using system defaults")
                ka_args = (3,)
            ka_intvl = ka_args
            if try_setsockopt(self.socket, "enable", SOL_SOCKET, SO_KEEPALIVE, 1):
                try_setsockopt(self.socket, socket.IPPROTO_TCP, 0x10, ka_intvl)
        else:
            logging.error("keepalive: implementation %r not recognized or not supported", ka_sig)

    def attempt_connection(self):
        """
        Try connecting to the (host, port) tuples specified at construction time.
        """
        self.connection_error = False
        sleep_exp = 1
        connect_count = 0

        logging.info("attempt reconnection (%s, %s, %s)", self.running, self.socket, connect_count)
        while self.running and self.socket is None and (connect_count < self.__reconnect_attempts_max or
                                                        self.__reconnect_attempts_max == -1):
            for host_and_port in self.__host_and_ports:
                try:
                    logging.info("attempting connection to host %s, port %s", host_and_port[0], host_and_port[1])
                    #websocket.enableTrace(True)
                    self.current_host_and_port = host_and_port
                    path = "/"
                    if self.ws_path:
                        path = self.ws_path

                    header = {}
                    if self.header is not None:
                        header = self.header

                    if self.__need_ssl():
                        scheme = "wss"
                    else:
                        scheme = "ws"
                    self.socket = websocket.create_connection(
                        f"{scheme}://{host_and_port[0]}:{host_and_port[1]}{path}",
                        timeout=self.__timeout,
                        header=self.header,
                        sslopt=self.get_ssl()
                    )
                    logging.info("established connection to host %s, port %s", host_and_port[0], host_and_port[1])
                    break
                except (OSError, AssertionError, websocket._exceptions.WebSocketException) as exc:
                    self.socket = None
                    connect_count += 1
                    logging.warning("Could not connect to host %s, port %s: %s", host_and_port[0], host_and_port[1],
                                    str(exc), exc_info=logging.verbose)

            if self.socket is None:
                sleep_duration = (min(self.__reconnect_sleep_max,
                                      ((self.__reconnect_sleep_initial / (1.0 + self.__reconnect_sleep_increase))
                                       * math.pow(1.0 + self.__reconnect_sleep_increase, sleep_exp)))
                                  * (1.0 + random.random() * self.__reconnect_sleep_jitter))
                sleep_end = monotonic() + sleep_duration
                logging.debug("sleeping for %.1f seconds before attempting reconnect", sleep_duration)
                while self.running and monotonic() < sleep_end:
                    time.sleep(0.2)

                if sleep_duration < self.__reconnect_sleep_max:
                    sleep_exp += 1

        if not self.socket:
            raise ConnectFailedException()

    def set_ssl(self,
                for_hosts=[],
                key_file=None,
                cert_file=None,
                ca_certs=None,
                cert_validator=None,
                ssl_version=DEFAULT_SSL_VERSION,
                password=None):
        """
        Sets up SSL configuration for the given hosts. This ensures socket is wrapped in a SSL connection, raising an
        exception if the SSL module can't be found.

        :param for_hosts: a list of tuples describing hosts this SSL configuration should be applied to
        :param cert_file: the path to a X509 certificate
        :param key_file: the path to a X509 key file
        :param ca_certs: the path to the a file containing CA certificates to validate the server against.
                         If this is not set, server side certificate validation is not done.
        :param cert_validator: function which performs extra validation on the client certificate, for example
                               checking the returned certificate has a commonName attribute equal to the
                               hostname (to avoid man in the middle attacks).
                               The signature is: (OK, err_msg) = validation_function(cert, hostname)
                               where OK is a boolean, and cert is a certificate structure
                               as returned by ssl.SSLSocket.getpeercert()
        :param ssl_version: SSL protocol to use for the connection. This should be one of the PROTOCOL_x
                            constants provided by the ssl module. The default is ssl.PROTOCOL_TLSv1
        :param password: SSL password
        """
        if not ssl:
            raise Exception("SSL connection requested, but SSL library not found")

        for host_port in for_hosts:
            self.__ssl_params[host_port] = dict(key_file=key_file,
                                                cert_file=cert_file,
                                                ca_certs=ca_certs,
                                                cert_validator=cert_validator,
                                                ssl_version=ssl_version,
                                                password=password)

    def __need_ssl(self, host_and_port=None):
        """
        Whether current host needs SSL or not.

        :param (str,int) host_and_port: the host/port pair to check, default current_host_and_port
        """
        if not host_and_port:
            host_and_port = self.current_host_and_port

        return host_and_port in self.__ssl_params

    def get_ssl(self, host_and_port=None):
        """
        Get SSL params for the given host.

        :param (str,int) host_and_port: the host/port pair we want SSL params for, default current_host_and_port
        """
        if not host_and_port:
            host_and_port = self.current_host_and_port

        return self.__ssl_params.get(host_and_port)


class WSStompConnection(StompConnection12):
    """
    Represents a 1.2 connection (comprising transport plus 1.2 protocol class).
    See :py:class:`stomp.transport.Transport` for details on the initialisation parameters.
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
                 timeout=None,
                 heartbeats=(0, 0),
                 keepalive=None,
                 vhost=None,
                 auto_decode=True,
                 encoding="utf-8",
                 auto_content_length=True,
                 heart_beat_receive_scale=1.5,
                 bind_host_port=None,
                 ws=None,
                 ws_path=None,
                 header=None,
                 binary_mode=False):
        transport = WSTransport(host_and_ports, prefer_localhost, try_loopback_connect,
                              reconnect_sleep_initial, reconnect_sleep_increase, reconnect_sleep_jitter,
                              reconnect_sleep_max, reconnect_attempts_max, timeout,
                              keepalive, vhost, auto_decode, encoding, bind_host_port=bind_host_port,
                              header=header, ws_path=ws_path, binary_mode=binary_mode)
        BaseConnection.__init__(self, transport)
        Protocol12.__init__(self, transport, heartbeats, auto_content_length,
                            heart_beat_receive_scale=heart_beat_receive_scale)
