import unittest

import stomp
from stomp.listener import TestListener, WaitingListener
from stomp.test.testutils import *


class TestRabbitMQSend(unittest.TestCase):

    def setUp(self):
        pass

    def testbasic(self):
        conn = stomp.Connection11(get_rabbitmq_host())
        listener = TestListener('123', print_to_log=True)
        listener2 = WaitingListener('456')
        conn.set_listener('123', listener)
        conn.set_listener('456', listener2)
        conn.connect(get_rabbitmq_user(), get_rabbitmq_password(), wait=True)
        conn.subscribe(destination='/queue/test', id=1, ack='auto')

        conn.send(body='this is a test', destination='/queue/test', receipt='123')
        listener.wait_on_receipt()

        conn.disconnect(receipt='456')
        listener2.wait_on_receipt()

        self.assertTrue(listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assertTrue(listener.messages == 1, 'should have received 1 message')
        self.assertTrue(listener.errors == 0, 'should not have received any errors')
        self.assertTrue(listener.disconnects == 1, 'should have received 1 disconnect, was %s' % listener.disconnects)