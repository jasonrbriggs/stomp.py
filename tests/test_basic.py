import signal
import socket
from time import monotonic

import stomp
from stomp.listener import TestListener
from .testutils import *


@pytest.fixture()
def testlistener():
    yield TestListener("123", print_to_log=True)


@pytest.fixture()
def conn(testlistener):
    conn = stomp.Connection11(get_default_host())
    conn.set_listener("testlistener", testlistener)
    conn.connect(get_default_user(), get_default_password(), wait=True)
    yield conn
    conn.disconnect(receipt=None)


@pytest.fixture()
def invalidconn(testlistener):
    conn = stomp.Connection([("192.0.2.0", 60000)], timeout=5, reconnect_attempts_max=1)
    conn.set_listener("testlistener", testlistener)
    yield conn


@pytest.fixture()
def ipv4only(monkeypatch):
    """
    Filter DNS requests to return only IPv4 results. This is useful to avoid long timeouts
    when tests attempt to connect to the IPv6 address, but the service is only listening
    on the IPv4 address.
    """
    real_getaddrinfo = socket.getaddrinfo
    def getaddrinfo_ipv4(*args, **kw):
        return [a for a in real_getaddrinfo(*args, **kw) if a[0] == socket.AF_INET]
    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo_ipv4)


class TestBasic(object):

    def test_subscribe_and_send(self, conn, testlistener):
        queuename = "/queue/test1-%s" % testlistener.timestamp
        conn.subscribe(destination=queuename, id=1, ack="auto")

        conn.send(body='{"val": "this is a test"}', destination=queuename,
                  content_type="application/json", receipt="123")

        validate_send(conn)

        (headers, body) = testlistener.get_latest_message()
        assert "content-type" in headers
        assert headers["content-type"] == "application/json"

    def test_default_to_localhost(self, ipv4only):
        conn = stomp.Connection()
        listener = TestListener("123", print_to_log=True)
        queuename = "/queue/test1-%s" % listener.timestamp
        conn.set_listener("testlistener", listener)
        conn.connect(get_rabbitmq_user(), get_rabbitmq_password(), wait=True)
        conn.send(body="this is a test", destination=queuename, receipt="123")
        conn.disconnect(receipt=None)

    def test_commit(self, conn):
        timestamp = time.strftime("%Y%m%d%H%M%S")
        queuename = "/queue/test2-%s" % timestamp
        conn.subscribe(destination=queuename, id=1, ack="auto")
        trans_id = conn.begin()
        conn.send(body="this is a test1", destination=queuename, transaction=trans_id)
        conn.send(body="this is a test2", destination=queuename, transaction=trans_id)
        conn.send(body="this is a test3", destination=queuename, transaction=trans_id, receipt="123")

        time.sleep(3)

        listener = conn.get_listener("testlistener")

        assert listener.connections == 1, "should have received 1 connection acknowledgement"
        assert listener.messages == 0, "should not have received any messages"

        conn.commit(transaction=trans_id)
        listener.wait_for_message(3)
        
        assert listener.messages == 3, "should have received 3 messages"
        assert listener.errors == 0, "should not have received any errors"

    def test_abort(self, conn):
        timestamp = time.strftime("%Y%m%d%H%M%S")
        queuename = "/queue/test3-%s" % timestamp
        conn.subscribe(destination=queuename, id=1, ack="auto")
        trans_id = conn.begin()
        conn.send(body="this is a test1", destination=queuename, transaction=trans_id)
        conn.send(body="this is a test2", destination=queuename, transaction=trans_id)
        conn.send(body="this is a test3", destination=queuename, transaction=trans_id)

        time.sleep(3)

        listener = conn.get_listener("testlistener")

        assert listener.connections == 1, "should have received 1 connection acknowledgement"
        assert listener.messages == 0, "should not have received any messages"

        conn.abort(transaction=trans_id)
        time.sleep(3)

        assert listener.messages == 0, "should not have received any messages"
        assert listener.errors == 0, "should not have received any errors"

    def test_timeout(self, invalidconn):
        ms = monotonic()
        try:
            invalidconn.connect("test", "test", wait=True)
            pytest.fail("shouldn't happen")
        except stomp.exception.ConnectFailedException:
            pass  # success!

    def test_childinterrupt(self, conn):
        def childhandler(signum, frame):
            print("received child signal")

        oldhandler = signal.signal(signal.SIGCHLD, childhandler)

        timestamp = time.strftime("%Y%m%d%H%M%S")
        queuename = "/queue/test5-%s" % timestamp
        conn.subscribe(destination=queuename, id=1, ack="auto", receipt="123")

        listener = conn.get_listener("testlistener")
        listener.wait_on_receipt()

        conn.send(body="this is an interrupt test 1", destination=queuename)

        print("causing signal by starting child process")
        os.system("sleep 1")

        time.sleep(1)

        signal.signal(signal.SIGCHLD, oldhandler)
        print("completed signal section")

        conn.send(body="this is an interrupt test 2", destination=queuename, receipt="123")

        listener.wait_for_message()

        assert listener.connections == 1, "should have received 1 connection acknowledgment"
        assert listener.errors == 0, "should not have received any errors"
        assert conn.connected, "should still be connected to STOMP provider"

    def test_clientack(self, conn):
        timestamp = time.strftime("%Y%m%d%H%M%S")
        queuename = "/queue/testclientack-%s" % timestamp
        conn.subscribe(destination=queuename, id=1, ack="client")

        conn.send(body="this is a test", destination=queuename, receipt="123")

        listener = conn.get_listener("testlistener")
        listener.wait_for_message()

        (headers, _) = listener.get_latest_message()

        message_id = headers["message-id"]
        subscription = headers["subscription"]

        conn.ack(message_id, subscription)

    def test_clientnack(self, conn):
        timestamp = time.strftime("%Y%m%d%H%M%S")
        queuename = "/queue/testclientnack-%s" % timestamp
        conn.subscribe(destination=queuename, id=1, ack="client")

        conn.send(body="this is a test", destination=queuename, receipt="123")

        listener = conn.get_listener("testlistener")
        listener.wait_for_message()

        (headers, _) = listener.get_latest_message()

        message_id = headers["message-id"]
        subscription = headers["subscription"]

        conn.nack(message_id, subscription)

    def test_specialchars(self, conn):
        timestamp = time.strftime("%Y%m%d%H%M%S")
        queuename = "/queue/testspecialchars-%s" % timestamp
        conn.subscribe(destination=queuename, id=1, ack="client")

        hdrs = {
            "special-1": "test with colon : test",
            "special-2": "test with backslash \\ test",
            "special-3": "test with newline \n"
        }

        conn.send(body="this is a test", headers=hdrs, destination=queuename, receipt="123")

        listener = conn.get_listener("testlistener")
        listener.wait_for_message()

        (headers, _) = listener.get_latest_message()

        _ = headers["message-id"]
        _ = headers["subscription"]
        assert "special-1" in headers
        assert "test with colon : test" == headers["special-1"]
        assert "special-2" in headers
        assert "test with backslash \\ test" == headers["special-2"]
        assert "special-3" in headers
        assert "test with newline \n" == headers["special-3"]

    def test_host_bind_port(self, ipv4only):
        conn = stomp.Connection(bind_host_port=("localhost", next_free_port()))
        listener = TestListener("981", print_to_log=True)
        queuename = "/queue/testbind-%s" % listener.timestamp
        conn.set_listener("testlistener", listener)
        conn.connect(get_rabbitmq_user(), get_rabbitmq_password(), wait=True)
        conn.send(body="this is a test using local bind port", destination=queuename, receipt="981")
        conn.disconnect(receipt=None)


class TestConnectionErrors(object):
    def test_connect_wait_error(self):
        conn = stomp.Connection(get_default_host())
        try:
            conn.connect("invalid", "user", True)
            pytest.fail("Shouldn't happen")
        except:
            pass

    def test_connect_nowait_error(self):
        conn = stomp.Connection(get_default_host())
        try:
            conn.connect("invalid", "user", False)
            assert not conn.connected, "Should not be connected"
        except:
            pytest.fail("Shouldn't happen")
