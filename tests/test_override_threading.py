import logging
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

import stomp
from stomp.listener import TestListener
from .testutils import *


executor = ThreadPoolExecutor()


def create_thread(fc):
    f = executor.submit(fc)
    print("Created future %s on executor %s" % (f, executor))
    return f


class ReconnectListener(TestListener):
    def __init__(self, conn):
        TestListener.__init__(self, "123", True)
        self.conn = conn
    def on_receiver_loop_ended(self, *args):
        if self.conn:
            c = self.conn
            self.conn = None
            c.connect(get_default_user(), get_default_password(), wait=True)
            c.disconnect()


@pytest.fixture
def conn():
    conn = stomp.Connection(get_default_host())

    # check thread override here
    conn.transport.override_threading(create_thread)

    listener = ReconnectListener(conn)
    conn.set_listener("testlistener", listener)
    conn.connect(get_default_user(), get_default_password(), wait=True)
    yield conn


class TestThreadingOverride(object):
    def test_threading(self, conn):
        listener = conn.get_listener("testlistener")
        queuename = "/queue/test1-%s" % listener.timestamp
        conn.subscribe(destination=queuename, id=1, ack="auto")

        conn.send(body="this is a test", destination=queuename, receipt="123")

        validate_send(conn, 1, 1, 0)

        logging.info("first disconnect")
        conn.disconnect(receipt="112233")

        logging.info("reconnecting")
        conn.connect(get_default_user(), get_default_password(), wait=True)

        logging.info("second disconnect")
        conn.disconnect()
