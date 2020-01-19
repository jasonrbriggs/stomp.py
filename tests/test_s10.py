import time

import pytest

import stomp
from stomp.listener import *
from .testutils import *


@pytest.fixture()
def conn():
    conn = stomp.Connection10(get_default_host())
    listener = TestListener("123", print_to_log=True)
    conn.set_listener("testlistener", listener)
    conn.connect(get_default_user(), get_default_password(), wait=True)
    yield conn
    conn.disconnect(receipt=None)

class Test10Connect(object):

    def testsend10(self, conn):
        listener = conn.get_listener("testlistener")
        queuename = "/queue/testsend10-%s" % listener.timestamp
        conn.subscribe(destination=queuename, ack="auto")

        conn.send(body="this is a test using protocol 1.0", destination=queuename, receipt="123")

        validate_send(conn, 1, 1, 0)

    def testclientack10(self, conn):
        listener = conn.get_listener("testlistener")
        queuename = "/queue/testclientack10-%s" % listener.timestamp
        conn.subscribe(destination=queuename, id=1, ack="client")

        conn.send(body="this is a test", destination=queuename)

        listener.wait_for_message()

        (headers, _) = listener.get_latest_message()

        message_id = headers["message-id"]

        conn.ack(message_id)

        time.sleep(1)
