import signal
import time
from time import monotonic

import pytest

import stomp
from stomp.listener import TestListener
from .testutils import *


class TestContext(object):
    timestamp = time.strftime("%Y%m%d%H%M%S")

    def send_test_message(self, conn):
        listener = TestListener("123", print_to_log=True)
        conn.set_listener("testlistener", listener)
        conn.connect(get_default_user(), get_default_password(), wait=True)

        queuename = "/queue/test1-%s" % self.timestamp
        conn.subscribe(destination=queuename, id=1, ack="auto")
        conn.send(body="this is a test", destination=queuename, receipt="123")
        listener.wait_for_message()

    def after_test_message(self, conn):
        conn.remove_listener("testlistener")

    def check_asserts(self, conn):
        listener = conn.get_listener("testlistener")
        assert listener.connections == 1, "should have received 1 connection acknowledgement"
        assert listener.disconnects >= 1, "should have received 1 disconnect"

    def test_with_context_stomp11(self):
        with stomp.Connection11(get_default_host()) as conn:
            self.send_test_message(conn)
        self.check_asserts(conn)
        self.after_test_message(conn)

    def test_with_context_stomp10(self):
        with stomp.Connection10(get_default_host()) as conn:
            self.send_test_message(conn)
        self.check_asserts(conn)
        self.after_test_message(conn)

    def test_with_context_stomp12(self):
        with stomp.Connection12(get_default_host()) as conn:
            self.send_test_message(conn)
        self.check_asserts(conn)
        self.after_test_message(conn)

