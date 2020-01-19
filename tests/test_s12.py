import pytest

import stomp
from stomp import exception
from stomp.listener import TestListener
from .testutils import *


@pytest.fixture()
def conn():
    conn = stomp.Connection12(get_default_host())
    listener = TestListener("123", print_to_log=True)
    conn.set_listener("testlistener", listener)
    conn.connect(get_default_user(), get_default_password(), wait=True)
    yield conn
    conn.disconnect(receipt=None)


class Test12Connect(object):

    def test_send(self, conn):
        listener = conn.get_listener("testlistener")
        queuename = "/queue/testsend12-%s" % listener.timestamp
        conn.subscribe(destination=queuename, id=1, ack="auto")

        conn.send(body="this is a test using protocol 1.2", destination=queuename, receipt="123")

        validate_send(conn, 1, 1, 0)

    def test_clientack(self, conn):
        listener = conn.get_listener("testlistener")
        queuename = "/queue/testclientack12-%s" % listener.timestamp
        conn.subscribe(destination=queuename, id=1, ack="client-individual")

        conn.send(body="this is a test", destination=queuename, receipt="123")

        listener.wait_for_message()

        (headers, _) = listener.get_latest_message()

        ack_id = headers["ack"]

        conn.ack(ack_id)

    def test_clientnack(self, conn):
        listener = conn.get_listener("testlistener")
        queuename = "/queue/testclientnack12-%s" % listener.timestamp
        conn.subscribe(destination=queuename, id=1, ack="client-individual")

        conn.send(body="this is a test", destination=queuename, receipt="123")

        listener.wait_for_message()

        (headers, _) = listener.get_latest_message()

        ack_id = headers["ack"]

        conn.nack(ack_id)


    def test_should_send_extra_header_clientnack(self, conn, mocker):
        listener = conn.get_listener("testlistener")
        queuename = "/queue/testclientnack12-%s" % listener.timestamp
        conn.subscribe(destination=queuename, id=1, ack="client-individual")

        conn.send(body="this is a test", destination=queuename, receipt="123")

        listener.wait_for_message()

        (headers, _) = listener.get_latest_message()

        ack_id = headers["ack"]

        wrapped_send_frame = mocker.patch.object(conn, "send_frame", wraps=conn.send_frame)
        conn.nack(ack_id, requeue="false")
        expected_headers = {HDR_ID: ack_id.replace(':', '\\c'), "requeue": "false"}
        wrapped_send_frame.assert_called_with(CMD_NACK, expected_headers)

    def test_timeout(self):
        server = StubStompServer("127.0.0.1", 60000)
        try:
            server.start()

            server.add_frame('''ERROR
message: connection failed\x00''')

            conn = stomp.Connection12([("127.0.0.1", 60000)])
            listener = TestListener(print_to_log=True)
            conn.set_listener('', listener)
            try:
                conn.connect(wait=True)
                self.fail("shouldn't happen")
            except exception.ConnectFailedException:
                pass
        finally:
            server.stop()

    def test_specialchars(self, conn):
        listener = conn.get_listener("testlistener")
        queuename = "/queue/testspecialchars12-%s" % listener.timestamp
        conn.subscribe(destination=queuename, id=1, ack="client")

        hdrs = {
            "special-1": "test with colon : test",
            "special-2": "test with backslash \\ test",
            "special-3": "test with newlines \n \n",
            "special-4": "test with carriage return \r"
        }

        conn.send(body="this is a test", headers=hdrs, destination=queuename, receipt="123")

        listener.wait_for_message()

        (headers, _) = listener.get_latest_message()

        _ = headers["message-id"]
        _ = headers["subscription"]
        assert "special-1" in headers
        assert "test with colon : test" == headers["special-1"]
        assert "special-2" in headers
        assert "test with backslash \\ test" == headers["special-2"]
        assert "special-3" in headers
        assert "test with newlines \n \n" == headers["special-3"]
        assert "special-4" in headers
        cr_header = headers["special-4"].replace('\\r', '\r')
        assert "test with carriage return \r" == cr_header

    def test_suppress_content_length(self, conn, mocker):
        listener = conn.get_listener("testlistener")
        queuename = "/queue/testspecialchars12-%s" % listener.timestamp
        conn = stomp.Connection12(get_default_host(), vhost=get_default_vhost(), auto_content_length=False)
        conn.transport = mocker.Mock()

        conn.send(body="test", destination=queuename, receipt="123")

        args, kwargs = conn.transport.transmit.call_args
        frame = args[0]
        assert "content-length" not in frame.headers
