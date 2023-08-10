import pytest
import time
import stomp
from stomp.listener import ConnectionListener, TestListener
from .testutils import get_ssl_host, get_default_user, get_default_password


class TimeoutListener(ConnectionListener):

    def __init__(self, listener):
        self.listener = listener

    def on_connected(self, frame):
        self.num = 3

    def on_heartbeat(self):
        self.num -= 1
        if self.num == 0:
            stomp.logging.info("Cutting receive_sleep in half")
            self.listener.receive_sleep = self.listener.receive_sleep / 2.0


@pytest.fixture()
def conn():
    conn = stomp.Connection12(get_ssl_host(), heartbeats=(0, 100))
    conn.set_ssl(get_ssl_host())
    listener = TestListener("123", print_to_log=True)
    conn.set_listener("testlistener", listener)
    conn.set_listener("timeout", TimeoutListener(conn.get_listener("protocol-listener")))
    conn.connect(get_default_user(), get_default_password(), wait=True)
    yield conn
    if conn.is_connected():
        conn.disconnect(receipt=None)


class TestHeartbeatTimeout(object):

    def test_heartbeat_timeout(self, conn):
        listener = conn.get_listener("testlistener")
        listener.wait_on_disconnected()
        # The socket can be disconnected before the heartbeat thread has a chance to
        # notify the listeners.
        time.sleep(0.1)
        assert listener.heartbeat_timeouts >= 1

    def test_heartbeat_timeout_reconnect(self, conn):
        listener = conn.get_listener("testlistener")
        listener.wait_on_disconnected()
        # Give the receive loop a chance to cleanup the socket.
        while conn.transport.socket:
            time.sleep(0.1)
        conn.connect(get_default_user(), get_default_password(), wait=True)
        assert listener.connections == 2

    def test_heartbeat_timeout_reconnect_loop(self, conn):
        listener = conn.get_listener("testlistener")
        while listener.connections < 20:
            listener.wait_on_disconnected()
            while conn.transport.socket:
                time.sleep(0.1)
            conn.connect(get_default_user(), get_default_password(), wait=True)
