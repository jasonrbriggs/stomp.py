from stomp.transport import *
from stomp.protocol import *
from stomp.listener import *
import uuid

##@namespace stomp.connect
# Main entry point for clients to create a STOMP connection.
#
# Provides connection classes for 1.0, 1.1, and 1.2 versions of the STOMP protocol.

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
    Represents a 1.2 connection (comprising transport plus 1.2 protocol class)
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
        \see stomp::transport::Transport.__init__
        \see stomp::protocol::Protocol12.__init__
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
