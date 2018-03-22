import unittest

import stomp
from stomp.listener import TestListener
from stomp.test.testutils import *


class TestRabbitMQSend(unittest.TestCase):

    def setUp(self):
        pass

    def testbasic(self):
        conn = stomp.Connection11(get_rabbitmq_host())
        listener = TestListener('123')
        conn.set_listener('', listener)
        conn.connect(get_rabbitmq_user(), get_rabbitmq_password(), wait=True)
        conn.subscribe(destination='/queue/test', id=1, ack='auto')

        conn.send(body='this is a test', destination='/queue/test', receipt='123')

        listener.wait_on_receipt()
        conn.disconnect(receipt=None)

        self.assertTrue(listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assertTrue(listener.messages == 1, 'should have received 1 message')
        self.assertTrue(listener.errors == 0, 'should not have received any errors')

    def test_clientnack_requeue(self):
        conn = stomp.Connection11(get_rabbitmq_host())
        listener = TestListener('123')
        conn.set_listener('', listener)
        conn.connect(get_rabbitmq_user(), get_rabbitmq_password(), wait=True)
        queuename = '/queue/testnack'
        conn.subscribe(destination=queuename, id=1, ack='client')
        conn.send(body='this is a test', destination=queuename, receipt='123')

        # Get the sent message
        listener.wait_for_message()
        (headers, _) = listener.get_latest_message()
        message_id = headers['message-id']
        subscription = headers['subscription']
        self.assertTrue(listener.messages == 1, 'should have received 1 message')

        # Nack with requeue=True, now the message should be again waiting in the queue
        conn.nack(message_id, subscription, requeue=True)

        # Get the requeued message
        listener.wait_for_message()
        (headers, _) = listener.get_latest_message()
        message_id = headers['message-id']
        subscription = headers['subscription']
        self.assertTrue(listener.messages == 2, 'should have received 2 messages')

        # Clean up
        conn.nack(message_id, subscription, requeue=False)
        listener.wait_on_receipt()
        conn.disconnect(receipt=None)
        self.assertTrue(listener.errors == 0, 'should not have received any errors')
