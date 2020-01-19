import time

import pytest

from stomp.adapter.multicast import MulticastConnection
from stomp.listener import TestListener
from stomp.utils import get_uuid
from .testutils import *


@pytest.fixture
def conn():
    conn = MulticastConnection()
    listener = TestListener("123", print_to_log=True)
    conn.set_listener("testlistener", listener)
    conn.connect()
    yield conn
    conn.disconnect(receipt=None)


@pytest.fixture
def connutf16():
    conn = MulticastConnection(encoding="utf-16")
    listener = TestListener("123", print_to_log=True)
    conn.set_listener("testlistener", listener)
    conn.connect()
    yield conn
    conn.disconnect(receipt=None)


class TestMulticast(object):

    def testsubscribe(self, conn):
        listener = conn.get_listener("testlistener")
        queuename = "/queue/test1-%s" % listener.timestamp
        conn.subscribe(destination=queuename, id=1, ack="auto")

        conn.send(body="this is a test", destination=queuename, receipt="123")

        validate_send(conn, 1, 1, 0)

    def testunsubscribe(self, conn):
        listener = conn.get_listener("testlistener")
        queuename = "/queue/test1-%s" % listener.timestamp
        conn.subscribe(destination=queuename, id=1, ack="auto")

        conn.send(body="this is a test", destination=queuename, receipt="123")

        validate_send(conn, 1, 1, 0)

        conn.unsubscribe(1)

        conn.send(body="this is a test", destination=queuename, receipt="124")

        time.sleep(3)

        assert listener.messages == 1, "should have only received 1 message"

    def testtransactions(self, conn):
        listener = conn.get_listener("testlistener")
        queuename = "/queue/test1-%s" % listener.timestamp
        conn.subscribe(destination=queuename, id=1, ack="auto")

        trans_id = get_uuid()
        conn.begin(trans_id)

        conn.send(body="this is a test", transaction=trans_id, destination=queuename, receipt="123")

        time.sleep(1)

        assert listener.messages == 0, "should not have received any messages"

        conn.commit(trans_id)

        listener.wait_on_receipt()

        assert listener.messages == 1, "should have received 1 message"

        conn.begin(trans_id)

        conn.send(body="this is a test", transaction=trans_id, destination=queuename, receipt="124")

        conn.abort(trans_id)

        time.sleep(3)

        assert listener.messages == 1, "should have only received 1 message"


class TestNonAsciiViaMulticast(object):

    def test_send_nonascii_auto_encoding(self, connutf16):
        listener = connutf16.get_listener("testlistener")
        queuename = "/queue/multicast-nonascii-%s" % listener.timestamp
        connutf16.subscribe(destination=queuename, ack="auto", id="1")

        txt = test_text_for_utf16
        connutf16.send(body=txt, destination=queuename, receipt="123")

        listener.wait_for_message()

        assert listener.connections >= 1, "should have received 1 connection acknowledgement"
        assert listener.messages >= 1, "should have received 1 message"
        assert listener.errors == 0, "should not have received any errors"

        (_, msg) = listener.get_latest_message()

        assert txt.encode("utf-8") == msg
