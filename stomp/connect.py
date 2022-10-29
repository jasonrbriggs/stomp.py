"""Main entry point for clients to create a STOMP connection.

Provides connection classes for `1.0 <http://stomp.github.io/stomp-specification-1.0.html>`_,
`1.1 <http://stomp.github.io/stomp-specification-1.1.html>`_, and
`1.2 <http://stomp.github.io/stomp-specification-1.2.html>`_ versions of the STOMP protocol.
"""


import asyncio
from collections import OrderedDict
import math
import random
import threading
import time
from time import monotonic

try:
    from socket import SOL_SOCKET, SO_KEEPALIVE, SOL_TCP, TCP_KEEPIDLE, TCP_KEEPINTVL, TCP_KEEPCNT
    LINUX_KEEPALIVE_AVAIL = True
except ImportError:
    LINUX_KEEPALIVE_AVAIL = False

try:
    from socket import IPPROTO_TCP
    MAC_KEEPALIVE_AVAIL = True
except ImportError:
    MAC_KEEPALIVE_AVAIL = False

try:
    import ssl
    from ssl import SSLError
    DEFAULT_SSL_VERSION = ssl.PROTOCOL_TLS_CLIENT
except (ImportError, AttributeError):
    ssl = None
    class SSLError(object):
        pass
    DEFAULT_SSL_VERSION = None

from stomp.listener import *
from stomp.utils import *
from stomp.constants import *
from stomp import exception
from stomp import logging


class StompProtocol(asyncio.Protocol):
    def __init__(self, listeners, on_con_lost, auto_decode, encoding):
        self.listeners = listeners
        self.__on_con_lost = on_con_lost
        self.transport = None
        self.__auto_decode = auto_decode
        self.__encoding = encoding

    def connection_made(self, transport):
        self.transport = transport

    def handle_frame(self, frame):
        for _, listener in self.listeners.items():
            listener.handle(frame)

    def data_received(self, data):
        split_data = data.split(b"\x00")
        single_msg = len(split_data) == 1
        for d in split_data:
            if not single_msg and d == b"":
                continue
            if d == b"":
                frame = HEARTBEAT_FRAME
            else:
                frame = parse_frame(d, self.__auto_decode, self.__encoding)
            self.handle_frame(frame)

    def transmit(self, frame):
        if self.transport is not None and not self.__on_con_lost.done():
            lines = convert_frame(frame, self.__encoding)
            packed_frame = pack(lines)
            self.transport.write(packed_frame + b"\x00")
            if logging.isEnabledFor(logging.DEBUG):
                logging.debug("sending frame: %s", clean_lines(lines))
            self.handle_frame(frame)
        else:
            raise exception.NotConnectedException()

    def connection_lost(self, exc):
        logging.debug("server closed the connection (%s)", exc)
        self.transport = None
        if not self.__on_con_lost.done():
            self.__on_con_lost.set_result(True)
            self.handle_frame(Frame(DISCONNECTED))


class BaseConnection(Listener):
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
                 bind_host_port=None):
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

        self.heartbeats = heartbeats

        self.timeout = timeout
        self.__connect_wait_condition = threading.Condition()
        self.connected = False
        self.connection_failed = False
        self.listeners = OrderedDict()
        self.protocol = None
        self.auto_content_length = auto_content_length
        self.blocking = None
        self.__auto_decode = auto_decode
        self.__encoding = encoding
        self.__receipts = {}
        self.__ssl_params = {}
        self.__keepalive = keepalive

    def __enter__(self):
        self.disconnect_receipt_id = get_uuid()
        self.disconnect_listener = WaitingListener(self.disconnect_receipt_id)
        self.set_listener("ZZZZZ-disconnect-listener", self.disconnect_listener)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect(self.disconnect_receipt_id)
        self.disconnect_listener.wait_on_receipt()
        self.disconnect_listener.wait_on_disconnected()

    def set_ssl(self,
                for_hosts=[],
                key_file=None,
                cert_file=None,
                ca_certs=None,
                cert_validator=None,
                ssl_version=DEFAULT_SSL_VERSION,
                password=None):
        """
        Sets up SSL configuration for the given hosts. This ensures the connection uses an SSLContext.

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

    def set_receipt(self, receipt_id, value):
        if value:
            self.__receipts[receipt_id] = value
        elif receipt_id in self.__receipts:
            del self.__receipts[receipt_id]

    def __enable_keepalive(self, sock):
        def try_setsockopt(sock, name, fam, opt, val=None):
            if val is None:
                return True  # no value to set always works
            try:
                sock.setsockopt(fam, opt, val)
                logging.debug("keepalive: set %r option to %r on socket", name, val)
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
                logging.debug("keepalive: autodetected linux-style support")
            elif MAC_KEEPALIVE_AVAIL:
                ka_sig = "mac"
                ka_args = None
                logging.debug("keepalive: autodetected mac-style support")
            else:
                logging.error("keepalive: unable to detect any implementation, DISABLED!")
                return

        if ka_sig == "linux":
            logging.debug("keepalive: activating linux-style support")
            if ka_args is None:
                logging.debug("keepalive: using system defaults")
                ka_args = (None, None, None)
            ka_idle, ka_intvl, ka_cnt = ka_args
            if try_setsockopt(sock, "enable", SOL_SOCKET, SO_KEEPALIVE, 1):
                try_setsockopt(sock, "idle time", SOL_TCP, TCP_KEEPIDLE, ka_idle)
                try_setsockopt(sock, "interval", SOL_TCP, TCP_KEEPINTVL, ka_intvl)
                try_setsockopt(sock, "count", SOL_TCP, TCP_KEEPCNT, ka_cnt)
        elif ka_sig == "mac":
            logging.debug("keepalive: activating mac-style support")
            if ka_args is None:
                logging.debug("keepalive: using system defaults")
                ka_args = (3,)
            ka_intvl = ka_args
            if try_setsockopt(sock, "enable", SOL_SOCKET, SO_KEEPALIVE, 1):
                try_setsockopt(sock, socket.IPPROTO_TCP, 0x10, ka_intvl)
        else:
            logging.error("keepalive: implementation %r not recognized or not supported", ka_sig)

    def __fail_connection(self):
        self.connected = False
        self.connection_failed = True
        with self.__connect_wait_condition:
            self.__connect_wait_condition.notify_all()

    def __attempt_connection(self):
        """
        Try connecting to the (host, port) tuples specified at construction time.
        """
        self.connection_error = False
        sleep_exp = 1
        connect_count = 0

        self.connected = False
        self.connection_failed = False

        sock = None
        logging.debug("attempt reconnection (%s)", connect_count)
        while sock is None and (connect_count < self.__reconnect_attempts_max or
                                self.__reconnect_attempts_max == -1):
            for host_and_port in self.__host_and_ports:
                try:
                    logging.debug("attempting connection to host %s, port %s", host_and_port[0], host_and_port[1])
                    if self.__bind_host_port:
                        sock = socket.create_connection(host_and_port, self.__timeout, self.__bind_host_port)
                    else:
                        sock = socket.create_connection(host_and_port, self.__timeout)
                    self.__enable_keepalive(sock)
                    
                    sock.settimeout(self.__timeout)

                    if self.blocking is not None:
                        sock.setblocking(self.blocking)

                    self.current_host_and_port = host_and_port
                    logging.info("established connection to host %s, port %s", host_and_port[0], host_and_port[1])
                    break
                except (OSError, AssertionError):
                    connect_count += 1
                    logging.warning("could not connect to host %s, port %s", host_and_port[0], host_and_port[1],
                                    exc_info=logging.verbose)

            if sock is None:
                sleep_duration = (min(self.__reconnect_sleep_max,
                                      ((self.__reconnect_sleep_initial / (1.0 + self.__reconnect_sleep_increase))
                                       * math.pow(1.0 + self.__reconnect_sleep_increase, sleep_exp)))
                                  * (1.0 + random.random() * self.__reconnect_sleep_jitter))
                sleep_end = monotonic() + sleep_duration
                logging.debug("sleeping for %.1f seconds before attempting reconnect", sleep_duration)
                while monotonic() < sleep_end:
                    time.sleep(0.2)

                if sleep_duration < self.__reconnect_sleep_max:
                    sleep_exp += 1

        if not sock:
            self.__fail_connection()
        return sock

    def close(self):
        self.protocol.close()

    async def __main(self, username=None, passcode=None, headers=None, keyword_headers={}):
        loop = asyncio.get_running_loop()
        #loop.set_debug(True)

        on_con_lost = loop.create_future()

        self.protocol = StompProtocol(self.listeners, on_con_lost, self.__auto_decode, self.__encoding)
        self.set_listener('connection', self)
        for listener in self.listeners.values():
            await listener.start(self.protocol)

        sock = self.__attempt_connection()
        if not sock:
            return

        if self.__need_ssl(self.current_host_and_port):
            ssl_params = self.get_ssl(self.current_host_and_port)
            tls_context = ssl.SSLContext(DEFAULT_SSL_VERSION)
            if ssl_params["ca_certs"]:
                cert_validation = ssl.CERT_REQUIRED
                tls_context.load_verify_locations(ssl_params["ca_certs"])
            else:
                cert_validation = ssl.CERT_NONE

            certfile = ssl_params["cert_file"]
            keyfile = ssl_params["key_file"]
            password = ssl_params.get("password")
            if certfile and not keyfile:
                keyfile = certfile
            if certfile:
                tls_context.load_cert_chain(certfile, keyfile, password)
            if cert_validation is None or cert_validation == ssl.CERT_NONE:
                tls_context.check_hostname = False
            tls_context.verify_mode = cert_validation
            server_hostname = self.current_host_and_port[0]
            ssl_handshake_timeout = self.__timeout
        else:
            tls_context = None
            server_hostname = None
            ssl_handshake_timeout = None

        try:
            transport, protocol = await loop.create_connection(lambda: self.protocol, sock=sock, ssl=tls_context, server_hostname=server_hostname, ssl_handshake_timeout=ssl_handshake_timeout)
        except:
            self.__fail_connection()
            return

        #if need_ssl and ssl_params["cert_validator"]:
        #    cert = sock.getpeercert()
        #    (ok, errmsg) = ssl_params["cert_validator"](cert, host_and_port[0])
        #    if not ok:
        #        raise SSLError("Server certificate validation failed: %s", errmsg)

        headers = merge_headers(headers, keyword_headers)
        headers[HDR_ACCEPT_VERSION] = self.version

        if username is not None:
            headers[HDR_LOGIN] = username

        if passcode is not None:
            headers[HDR_PASSCODE] = passcode

        protocol.transmit(Frame(self.connect_command, headers))

        try:
            await on_con_lost
        finally:
            transport.close()

    def wait_for_connection(self):
        """
        Wait until we've established a connection with the server.

        :param float timeout: how long to wait, in seconds
        """
        if self.timeout is not None:
            wait_time = self.timeout / 10.0
        else:
            wait_time = None
        with self.__connect_wait_condition:
            while not self.connected and not self.connection_failed:
                self.__connect_wait_condition.wait(wait_time)
        if self.connection_failed:
            raise exception.ConnectFailedException()

    def connect(self, username=None, passcode=None, wait=False, headers=None,
                with_connect_command=False, **keyword_headers):
        thread = threading.Thread(None, async_run, args=(self.__main, username, passcode, headers, keyword_headers))
        thread.daemon = True
        thread.start()

        if wait:
            self.wait_for_connection()

    def on_connected(self, frame):
        with self.__connect_wait_condition:
            Listener.on_connected(self, frame)
            self.__connect_wait_condition.notify_all()

    def on_error(self, frame):
        if not self.connected:
            with self.__connect_wait_condition:
                self.connection_failed = True
                self.__connect_wait_condition.notify_all()

    def set_listener(self, name, listener):
        self.listeners[name] = listener

    def get_listener(self, name):
        """
        Return the named listener

        :param str name: the listener to return

        :rtype: ConnectionListener
        """
        return self.listeners.get(name)

    def remove_listener(self, name):
        """
        :param str name:
        """
        del self.listeners[name]


class StompConnection11(BaseConnection, HeartbeatListener):
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
                 bind_host_port=None):
        BaseConnection.__init__(self, host_and_ports, prefer_localhost, try_loopback_connect, reconnect_sleep_initial,
                                reconnect_sleep_increase, reconnect_sleep_jitter, reconnect_sleep_max, reconnect_attempts_max,
                                timeout, heartbeats, keepalive, vhost, auto_decode, encoding, auto_content_length,
                                heart_beat_receive_scale, bind_host_port)
        HeartbeatListener.__init__(self, heartbeats, heart_beat_receive_scale)
        self.version = '1.1'
        self.connect_command = CMD_STOMP

    def abort(self, transaction, headers=None, **keyword_headers):
        """
        Abort a transaction.

        :param str transaction: the identifier of the transaction
        :param dict headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        """
        assert transaction is not None, "'transaction' is required"
        headers = merge_headers(headers, keyword_headers)
        headers[HDR_TRANSACTION] = transaction
        self.protocol.transmit(Frame(CMD_ABORT, headers))

    def ack(self, id, subscription, transaction=None, receipt=None):
        """
        Acknowledge 'consumption' of a message by id.

        :param str id: identifier of the message
        :param str subscription: the subscription this message is associated with
        :param str transaction: include the acknowledgement in the specified transaction
        :param str receipt: the receipt id
        """
        assert id is not None, "'id' is required"
        assert subscription is not None, "'subscription' is required"
        headers = {HDR_MESSAGE_ID: id, HDR_SUBSCRIPTION: subscription}
        if transaction:
            headers[HDR_TRANSACTION] = transaction
        if receipt:
            headers[HDR_RECEIPT] = receipt
        self.protocol.transmit(Frame(CMD_ACK, headers))

    def begin(self, transaction=None, headers=None, **keyword_headers):
        """
        Begin a transaction.

        :param str transaction: the identifier for the transaction (optional - if not specified
            a unique transaction id will be generated)
        :param dict headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires

        :return: the transaction id
        :rtype: str
        """
        headers = merge_headers(headers, keyword_headers)
        if not transaction:
            transaction = get_uuid()
        headers[HDR_TRANSACTION] = transaction
        self.protocol.transmit(Frame(CMD_BEGIN, headers))
        return transaction

    def commit(self, transaction=None, headers=None, **keyword_headers):
        """
        Commit a transaction.

        :param str transaction: the identifier for the transaction
        :param dict headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        """
        assert transaction is not None, "'transaction' is required"
        headers = merge_headers(headers, keyword_headers)
        headers[HDR_TRANSACTION] = transaction
        self.protocol.transmit(Frame(CMD_COMMIT, headers))

    def connect(self, username=None, passcode=None, wait=False, headers=None,
                with_connect_command=False, **keyword_headers):
        default_headers = {}
        if self.heartbeats != (0, 0):
            default_headers['heart-beat'] = '%s,%s' % self.heartbeats
        headers = merge_headers(default_headers, headers, keyword_headers)
        BaseConnection.connect(self, username, passcode, wait, headers, with_connect_command, **keyword_headers)

    def disconnect(self, receipt=None, headers=None, **keyword_headers):
        """
        Disconnect from the server.

        :param str receipt: the receipt to use (once the server acknowledges that receipt, we're
            officially disconnected; optional - if not specified a unique receipt id will
            be generated)
        :param dict headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        """
        if not self.connected:
            logging.debug("not sending disconnect, already disconnected")
            return
        headers = merge_headers(headers, keyword_headers)
        rec = receipt or get_uuid()
        headers[HDR_RECEIPT] = rec
        self.set_receipt(rec, CMD_DISCONNECT)
        self.protocol.transmit(Frame(CMD_DISCONNECT, headers))

    def nack(self, id, subscription, transaction=None, receipt=None, **keyword_headers):
        """
        Let the server know that a message was not consumed.

        :param str id: the unique id of the message to nack
        :param str subscription: the subscription this message is associated with
        :param str transaction: include this nack in a named transaction
        :param str receipt: the receipt id
        :param keyword_headers: any additional headers to send with the nack command
        """
        assert id is not None, "'id' is required"
        assert subscription is not None, "'subscription' is required"
        headers = {HDR_MESSAGE_ID: id, HDR_SUBSCRIPTION: subscription}
        headers = merge_headers(headers, keyword_headers)
        if transaction:
            headers[HDR_TRANSACTION] = transaction
        if receipt:
            headers[HDR_RECEIPT] = receipt
        self.protocol.transmit(Frame(CMD_NACK, headers))

    def send(self, destination, body, content_type=None, headers=None, **keyword_headers):
        """
        Send a message to a destination in the messaging system (as per
         https://stomp.github.io/stomp-specification-1.2.html#SEND)

        :param str destination: the destination (such as a message queue - for example
        '/queue/test' - or a message topic)
        :param body: the content of the message
        :param str content_type: the MIME type of message
        :param dict headers: additional headers to send in the message frame
        :param keyword_headers: any additional headers the broker requires
        """
        assert destination is not None, "'destination' is required"
        assert body is not None, "'body' is required"
        headers = merge_headers(headers, keyword_headers)
        headers[HDR_DESTINATION] = destination
        if content_type:
            headers[HDR_CONTENT_TYPE] = content_type
        if self.auto_content_length and body and HDR_CONTENT_LENGTH not in headers:
            headers[HDR_CONTENT_LENGTH] = len(body)
        self.protocol.transmit(Frame(CMD_SEND, headers, body))

    def subscribe(self, destination, id, ack="auto", headers=None, **keyword_headers):
        """
        Subscribe to a destination

        :param str destination: the topic or queue to subscribe to
        :param str id: the identifier to uniquely identify the subscription
        :param str ack: either auto, client or client-individual
        (see https://stomp.github.io/stomp-specification-1.2.html#SUBSCRIBE for more info)
        :param dict headers: a map of any additional headers to send with the subscription
        :param keyword_headers: any additional headers to send with the subscription
        """
        assert destination is not None, "'destination' is required"
        assert id is not None, "'id' is required"
        headers = merge_headers(headers, keyword_headers)
        headers[HDR_DESTINATION] = destination
        headers[HDR_ID] = id
        headers[HDR_ACK] = ack
        self.protocol.transmit(Frame(CMD_SUBSCRIBE, headers))

    def unsubscribe(self, id, headers=None, **keyword_headers):
        """
        Unsubscribe from a destination by its unique identifier

        :param str id: the unique identifier to unsubscribe from
        :param dict headers: additional headers to send with the unsubscribe
        :param keyword_headers: any additional headers to send with the subscription
        """
        assert id is not None, "'id' is required"
        headers = merge_headers(headers, keyword_headers)
        headers[HDR_ID] = id
        self.protocol.transmit(Frame(CMD_UNSUBSCRIBE, headers))

    def on_connected(self, frame):
        BaseConnection.on_connected(self, frame)
        HeartbeatListener.on_connected(self, frame)


class StompConnection12(StompConnection11):
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
                 bind_host_port=None):
        StompConnection11.__init__(self, host_and_ports, prefer_localhost, try_loopback_connect, reconnect_sleep_initial,
                                reconnect_sleep_increase, reconnect_sleep_jitter, reconnect_sleep_max, reconnect_attempts_max,
                                timeout, heartbeats, keepalive, vhost, auto_decode, encoding, auto_content_length,
                                heart_beat_receive_scale, bind_host_port)
        self.version = '1.2'

    def ack(self, id, transaction=None, receipt=None):
        """
        Acknowledge 'consumption' of a message by id.

        :param str id: identifier of the message
        :param str transaction: include the acknowledgement in the specified transaction
        :param str receipt: the receipt id
        """
        assert id is not None, "'id' is required"
        headers = {HDR_ID: id}
        if transaction:
            headers[HDR_TRANSACTION] = transaction
        if receipt:
            headers[HDR_RECEIPT] = receipt
        self.protocol.transmit(Frame(CMD_ACK, headers))

    def nack(self, id, transaction=None, receipt=None, **keyword_headers):
        """
        Let the server know that a message was not consumed.

        :param str id: the unique id of the message to nack
        :param str transaction: include this nack in a named transaction
        :param str receipt: the receipt id
        :param keyword_headers: any additional headers to send with the nack command
        """
        assert id is not None, "'id' is required"
        headers = {HDR_ID: id}
        headers = merge_headers(headers, keyword_headers)
        if transaction:
            headers[HDR_TRANSACTION] = transaction
        if receipt:
            headers[HDR_RECEIPT] = receipt
        self.protocol.transmit(Frame(CMD_NACK, headers))

    def send(self, destination, body, content_type=None, headers=None, **keyword_headers):
        """
        Send a message to a destination.

        :param str destination: the destination of the message (e.g. queue or topic name)
        :param body: the content of the message
        :param str content_type: the content type of the message
        :param dict headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        """
        assert destination is not None, "'destination' is required"
        assert body is not None, "'body' is required"
        headers = merge_headers(headers, keyword_headers)
        headers[HDR_DESTINATION] = destination
        if content_type:
            headers[HDR_CONTENT_TYPE] = content_type
        if self.auto_content_length and body and HDR_CONTENT_LENGTH not in headers:
            headers[HDR_CONTENT_LENGTH] = len(body)
        self.protocol.transmit(Frame(CMD_SEND, headers, body))

    def subscribe(self, destination, id, ack="auto", headers=None, **keyword_headers):
        """
        Subscribe to a destination

        :param str destination: the topic or queue to subscribe to
        :param str id: the identifier to uniquely identify the subscription
        :param str ack: either auto, client or client-individual
        (see https://stomp.github.io/stomp-specification-1.2.html#SUBSCRIBE for more info)
        :param dict headers: a map of any additional headers to send with the subscription
        :param keyword_headers: any additional headers to send with the subscription
        """
        assert destination is not None, "'destination' is required"
        assert id is not None, "'id' is required"
        headers = merge_headers(headers, keyword_headers)
        headers[HDR_DESTINATION] = destination
        headers[HDR_ID] = id
        headers[HDR_ACK] = ack
        self.protocol.transmit(Frame(CMD_SUBSCRIBE, headers))

    def unsubscribe(self, id, headers=None, **keyword_headers):
        """
        Unsubscribe from a destination by its unique identifier

        :param str id: the unique identifier to unsubscribe from
        :param dict headers: additional headers to send with the unsubscribe
        :param keyword_headers: any additional headers to send with the subscription
        """
        assert id is not None, "'id' is required"
        headers = merge_headers(headers, keyword_headers)
        headers[HDR_ID] = id
        self.protocol.transmit(Frame(CMD_UNSUBSCRIBE, headers))

