"""Main entry point for clients to create a STOMP connection.

Provides connection classes for `1.0 <http://stomp.github.io/stomp-specification-1.0.html>`_,
`1.1 <http://stomp.github.io/stomp-specification-1.1.html>`_, and
`1.2 <http://stomp.github.io/stomp-specification-1.2.html>`_ versions of the STOMP protocol.
"""

from stomp.protocol import *
from stomp.transport import *
from stomp.utils import get_uuid


class BaseConnection(Publisher):
    """
    Base class for all connection classes.
    """

    def __init__(self, transport):
        """
        :param Transport transport:
        """
        self.transport = transport

    def __enter__(self):
        self.disconnect_receipt_id = get_uuid()
        self.disconnect_listener = WaitingListener(self.disconnect_receipt_id)
        self.set_listener("ZZZZZ-disconnect-listener", self.disconnect_listener)
        return self

    def disconnect(self, receipt=None, headers=None, **keyword_headers): pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect(self.disconnect_receipt_id)
        self.disconnect_listener.wait_on_receipt()
        self.disconnect_listener.wait_on_disconnected()

    def set_listener(self, name, listener):
        """
        :param str name:
        :param ConnectionListener listener:
        """
        self.transport.set_listener(name, listener)

    def remove_listener(self, name):
        """
        :param str name:
        """
        self.transport.remove_listener(name)

    def get_listener(self, name):
        """
        :param str name:

        :rtype: ConnectionListener
        """
        return self.transport.get_listener(name)

    def is_connected(self):
        """
        :rtype: bool
        """
        return self.transport.is_connected()

    def set_receipt(self, receipt_id, value):
        self.transport.set_receipt(receipt_id, value)

    def set_ssl(self, *args, **kwargs):
        self.transport.set_ssl(*args, **kwargs)

    def get_ssl(self, host_and_port=None):
        return self.transport.get_ssl(host_and_port)


class StompConnection10(BaseConnection, Protocol10):
    """
    Represents a 1.0 connection (comprising transport plus 1.0 protocol class).
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
                 keepalive=None,
                 auto_decode=True,
                 encoding="utf-8",
                 auto_content_length=True,
                 bind_host_port=None):
        transport = Transport(host_and_ports, prefer_localhost, try_loopback_connect,
                              reconnect_sleep_initial, reconnect_sleep_increase, reconnect_sleep_jitter,
                              reconnect_sleep_max, reconnect_attempts_max, timeout,
                              keepalive, None, auto_decode, encoding, bind_host_port=bind_host_port)
        BaseConnection.__init__(self, transport)
        Protocol10.__init__(self, transport, auto_content_length)

    def connect(self, *args, **kwargs):
        self.transport.start()
        Protocol10.connect(self, *args, **kwargs)

    def disconnect(self, receipt=None, headers=None, **keyword_headers):
        """
        Call the protocol disconnection, and then stop the transport itself.

        :param str receipt: the receipt to use with the disconnect
        :param dict headers: a map of any additional headers to send with the disconnection
        :param keyword_headers: any additional headers to send with the disconnection
        """
        Protocol10.disconnect(self, receipt, headers, **keyword_headers)
        if receipt is not None:
            self.transport.stop()


class StompConnection11(BaseConnection, Protocol11):
    """
    Represents a 1.1 connection (comprising transport plus 1.1 protocol class)
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
                 bind_host_port=None):
        transport = Transport(host_and_ports, prefer_localhost, try_loopback_connect,
                              reconnect_sleep_initial, reconnect_sleep_increase, reconnect_sleep_jitter,
                              reconnect_sleep_max, reconnect_attempts_max, timeout,
                              keepalive, vhost, auto_decode, encoding, bind_host_port=bind_host_port)
        BaseConnection.__init__(self, transport)
        Protocol11.__init__(self, transport, heartbeats, auto_content_length,
                            heart_beat_receive_scale=heart_beat_receive_scale)

    def connect(self, *args, **kwargs):
        self.transport.start()
        Protocol11.connect(self, *args, **kwargs)

    def disconnect(self, receipt=None, headers=None, **keyword_headers):
        """
        Call the protocol disconnection, and then stop the transport itself.

        :param str receipt: the receipt to use with the disconnect
        :param dict headers: a map of any additional headers to send with the disconnection
        :param keyword_headers: any additional headers to send with the disconnection
        """
        Protocol11.disconnect(self, receipt, headers, **keyword_headers)
        if receipt is not None:
            self.transport.stop()


class StompConnection12(BaseConnection, Protocol12):
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
                 bind_host_port=None):
        transport = Transport(host_and_ports, prefer_localhost, try_loopback_connect,
                              reconnect_sleep_initial, reconnect_sleep_increase, reconnect_sleep_jitter,
                              reconnect_sleep_max, reconnect_attempts_max, timeout,
                              keepalive, vhost, auto_decode, encoding, bind_host_port=bind_host_port)
        BaseConnection.__init__(self, transport)
        Protocol12.__init__(self, transport, heartbeats, auto_content_length,
                            heart_beat_receive_scale=heart_beat_receive_scale)

    def connect(self, *args, **kwargs):
        self.transport.start()
        Protocol12.connect(self, *args, **kwargs)

    def disconnect(self, receipt=None, headers=None, **keyword_headers):
        """
        Call the protocol disconnection, and then stop the transport itself.

        :param str receipt: the receipt to use with the disconnect
        :param dict headers: a map of any additional headers to send with the disconnection
        :param keyword_headers: any additional headers to send with the disconnection
        """
        Protocol12.disconnect(self, receipt, headers, **keyword_headers)
        if receipt is not None:
            self.transport.stop()

    @staticmethod
    def is_eol(c):
        return c == b"\x0a" or c == b"\x0d\x0a"
