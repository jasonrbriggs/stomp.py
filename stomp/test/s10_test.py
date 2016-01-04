import time
import unittest

import stomp
from stomp.listener import TestListener
from stomp.test.testutils import *


class Test10Connect(unittest.TestCase):

    def setUp(self):
        conn = stomp.Connection10(get_default_host())
        listener = TestListener('123')
        conn.set_listener('', listener)
        conn.start()
        conn.connect(get_default_user(), get_default_password(), wait=True)
        self.conn = conn
        self.listener = listener
        self.timestamp = time.strftime('%Y%m%d%H%M%S')

    def tearDown(self):
        if self.conn:
            self.conn.disconnect(receipt=None)

    def testsend10(self):
        queuename = '/queue/testsend10-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, ack='auto')

        self.conn.send(body='this is a test using protocol 1.0', destination=queuename, receipt='123')

        self.listener.wait_for_message()

        self.assertTrue(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assertTrue(self.listener.messages == 1, 'should have received 1 message')
        self.assertTrue(self.listener.errors == 0, 'should not have received any errors')

    def testclientack10(self):
        queuename = '/queue/testclientack10-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='client')

        self.conn.send(body='this is a test', destination=queuename)

        self.listener.wait_for_message()

        (headers, _) = self.listener.get_latest_message()

        message_id = headers['message-id']

        self.conn.ack(message_id)

        time.sleep(1)
