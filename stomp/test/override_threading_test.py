import os
import signal
import time
import unittest

import stomp
from stomp import exception
from stomp.backward import monotonic
from stomp.listener import TestListener
from stomp.test.testutils import *

from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor()


def create_thread(fc):
    f = executor.submit(fc)
    print('Created future %s on executor %s' % (f, executor))
    return f


class ReconnectListener(TestListener):
    def __init__(self, conn):
        TestListener.__init__(self, '123')
        self.conn = conn
    def on_receiver_loop_ended(self, *args):
        if self.conn:
            c = self.conn
            self.conn = None
            c.connect(get_default_user(), get_default_password(), wait=True)
            c.disconnect()

class TestThreadingOverride(unittest.TestCase):

    def setUp(self):
        conn = stomp.Connection(get_default_host())

        # check thread override here
        conn.transport.override_threading(create_thread)

        listener = ReconnectListener(conn)
        conn.set_listener('', listener)
        conn.connect(get_default_user(), get_default_password(), wait=True)
        self.conn = conn
        self.listener = listener
        self.timestamp = time.strftime('%Y%m%d%H%M%S')

    def test_basic(self):
        queuename = '/queue/test1-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='auto')

        self.conn.send(body='this is a test', destination=queuename, receipt='123')

        self.listener.wait_for_message()

        self.assertTrue(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assertTrue(self.listener.messages == 1, 'should have received 1 message')
        self.assertTrue(self.listener.errors == 0, 'should not have received any errors')

        self.conn.disconnect(receipt=None)

        self.conn.connect(get_default_user(), get_default_password(), wait=True)
        self.conn.disconnect()