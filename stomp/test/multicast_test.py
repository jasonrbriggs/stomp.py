import time
import unittest
import uuid

from stomp.adapter.multicast import MulticastConnection
from stomp.listener import TestListener
from stomp.test.testutils import *


class TestMulticast(unittest.TestCase):

    def setUp(self):
        conn = MulticastConnection()
        listener = TestListener('123')
        conn.set_listener('', listener)
        conn.start()
        conn.connect()
        self.conn = conn
        self.listener = listener
        self.timestamp = time.strftime('%Y%m%d%H%M%S')

    def tearDown(self):
        if self.conn:
            self.conn.disconnect(receipt=None)

    def testsubscribe(self):
        queuename = '/queue/test1-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='auto')

        self.conn.send(body='this is a test', destination=queuename, receipt='123')

        self.listener.wait_on_receipt()

        self.assertTrue(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assertTrue(self.listener.messages == 1, 'should have received 1 message')
        self.assertTrue(self.listener.errors == 0, 'should not have received any errors')

    def testunsubscribe(self):
        queuename = '/queue/test1-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='auto')

        self.conn.send(body='this is a test', destination=queuename, receipt='123')

        self.listener.wait_on_receipt()

        self.assertTrue(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assertTrue(self.listener.messages == 1, 'should have received 1 message')
        self.assertTrue(self.listener.errors == 0, 'should not have received any errors')

        self.conn.unsubscribe(1)

        self.conn.send(body='this is a test', destination=queuename, receipt='124')

        time.sleep(3)

        self.assertTrue(self.listener.messages == 1, 'should have only received 1 message')

    def testtransactions(self):
        queuename = '/queue/test1-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='auto')

        trans_id = str(uuid.uuid4())
        self.conn.begin(trans_id)

        self.conn.send(body='this is a test', transaction=trans_id, destination=queuename, receipt='123')

        time.sleep(1)

        self.assertTrue(self.listener.messages == 0, 'should not have received any messages')

        self.conn.commit(trans_id)

        self.listener.wait_on_receipt()

        self.assertTrue(self.listener.messages == 1, 'should have received 1 message')

        self.conn.begin(trans_id)

        self.conn.send(body='this is a test', transaction=trans_id, destination=queuename, receipt='124')

        self.conn.abort(trans_id)

        time.sleep(3)

        self.assertTrue(self.listener.messages == 1, 'should have only received 1 message')
