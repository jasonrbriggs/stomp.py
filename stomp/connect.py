"""Main entry point for clients to create a STOMP connection.

Provides connection classes for 1.0, 1.1, and 1.2 versions of the STOMP protocol.
"""

from stomp.transport import *
from stomp.protocol import *
from stomp.listener import *
import uuid


class BaseConnection(Publisher):
    def __init__(self, transport):
        self.transport = transport

    def set_listener(self, name, listener):
        self.transport.set_listener(name, listener)

    def remove_listener(self, name):
        self.transport.remove_listener(name)

    def get_listener(self, name):
        return self.transport.get_listener(name)

    def start(self):
        self.transport.start()

    def stop(self):
        self.transport.stop()

    def is_connected(self):
        return self.transport.is_connected()

    def set_ssl(self, *args, **kwargs):
        self.transport.set_ssl(*args, **kwargs)

    def get_ssl(self, *args, **kwargs):
        self.transport.get_ssl(*args, **kwargs)


class StompConnection10(BaseConnection, Protocol10):
    """
    Represents a 1.0 connection (comprising transport plus 1.0 protocol class)
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
                 ssl_version=DEFAULT_SSL_VERSION,
                 timeout=None,
                 keepalive=None,
                 auto_decode=True):
        transport = Transport(host_and_ports, prefer_localhost, try_loopback_connect,
                              reconnect_sleep_initial, reconnect_sleep_increase, reconnect_sleep_jitter,
                              reconnect_sleep_max, reconnect_attempts_max, use_ssl, ssl_key_file, ssl_cert_file,
                              ssl_ca_certs, ssl_cert_validator, wait_on_receipt, ssl_version, timeout,
                              keepalive, None, auto_decode)
        BaseConnection.__init__(self, transport)
        Protocol10.__init__(self, transport)

    def disconnect(self, receipt=str(uuid.uuid4()), headers={}, **keyword_headers):
        Protocol10.disconnect(self, receipt, headers, **keyword_headers)
        self.transport.stop()


class StompConnection11(BaseConnection, Protocol11):
    """
    Represents a 1.1 connection (comprising transport plus 1.1 protocol class)
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
                 ssl_version=DEFAULT_SSL_VERSION,
                 timeout=None,
                 heartbeats=(0, 0),
                 keepalive=None,
                 vhost=None,
                 auto_decode=True):
        transport = Transport(host_and_ports, prefer_localhost, try_loopback_connect,
                              reconnect_sleep_initial, reconnect_sleep_increase, reconnect_sleep_jitter,
                              reconnect_sleep_max, reconnect_attempts_max, use_ssl, ssl_key_file, ssl_cert_file,
                              ssl_ca_certs, ssl_cert_validator, wait_on_receipt, ssl_version, timeout,
                              keepalive, vhost, auto_decode)
        BaseConnection.__init__(self, transport)
        Protocol11.__init__(self, transport, heartbeats)

    def disconnect(self, receipt=str(uuid.uuid4()), headers={}, **keyword_headers):
        Protocol11.disconnect(self, receipt, headers, **keyword_headers)
        self.transport.stop()


class StompConnection12(BaseConnection, Protocol12):
    """
    :param host_and_ports: a list of (host, port) tuples.
    :param prefer_localhost: if True and the local host is mentioned in the (host, port) tuples,
                             try to connect to this first
    :param try_loopback_connect: if True and the local host is found in the host tuples, try
                                 connecting to it using loopback interface (127.0.0.1)
    :param reconnect_sleep_initial: initial delay in seconds to wait before reattempting
                                    to establish a connection if connection to any of the hosts fails.
    :param reconnect_sleep_increase: factor by which the sleep delay is increased after
                                     each connection attempt. For example, 0.5 means
                                     to wait 50% longer than before the previous attempt,
                                     1.0 means wait twice as long, and 0.0 means keep
                                     the delay constant.
    :param reconnect_sleep_max: maximum delay between connection attempts, regardless
                                of the reconnect_sleep_increase.
    :param reconnect_sleep_jitter: random additional time to wait (as a percentage of
                                   the time determined using the previous parameters)
                                   between connection attempts in order to avoid
                                   stampeding. For example, a value of 0.1 means to wait
                                   an extra 0%-10% (randomly determined) of the delay
                                   calculated using the previous three parameters.
    :param reconnect_attempts_max: maximum attempts to reconnect
    :param use_ssl: deprecated, use the set_ssl method instead
    :param ssl_cert_file: deprecated, use the set_ssl method instead
    :param ssl_key_file: deprecated, use the set_ssl method instead
    :param ssl_ca_certs: deprecated, use the set_ssl method instead
    :param ssl_cert_validator: deprecated, use the set_ssl method instead
    :param ssl_version: deprecated, use the set_ssl method instead
    :param timeout: the timeout value to use when connecting the stomp socket
    :param keepalive: some operating systems support sending the occasional heart
                      beat packets to detect when a connection fails.  This
                      parameter can either be set set to a boolean to turn on the
                      default keepalive options for your OS, or as a tuple of
                      values, which also enables keepalive packets, but specifies
                      options specific to your OS implementation
    :param vhost: specify a virtual hostname to provide in the 'host' header of the connection
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
                 ssl_version=DEFAULT_SSL_VERSION,
                 timeout=None,
                 heartbeats=(0, 0),
                 keepalive=None,
                 vhost=None,
                 auto_decode=True):
        """
        Initialise a stomp version 1.2 connection
        """
        transport = Transport(host_and_ports, prefer_localhost, try_loopback_connect,
                              reconnect_sleep_initial, reconnect_sleep_increase, reconnect_sleep_jitter,
                              reconnect_sleep_max, reconnect_attempts_max, use_ssl, ssl_key_file, ssl_cert_file,
                              ssl_ca_certs, ssl_cert_validator, wait_on_receipt, ssl_version, timeout,
                              keepalive, vhost, auto_decode)
        BaseConnection.__init__(self, transport)
        Protocol12.__init__(self, transport, heartbeats)

    def disconnect(self, receipt=str(uuid.uuid4()), headers={}, **keyword_headers):
        Protocol12.disconnect(self, receipt, headers, **keyword_headers)
        self.transport.stop()
