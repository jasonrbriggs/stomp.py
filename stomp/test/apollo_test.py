import unittest

import stomp
from stomp.listener import TestListener
from stomp.test.testutils import *


class TestApolloSend(unittest.TestCase):

    def setUp(self):
        pass

    def testbasic(self):
        conn = stomp.Connection11(get_apollo_host())
        listener = TestListener('123')
        conn.set_listener('', listener)
        conn.connect(get_default_user(), get_default_password(), wait=True)
        conn.subscribe(destination='/queue/test', id=1, ack='auto')

        conn.send(body='this is a test', destination='/queue/test', receipt='123')

        listener.wait_on_receipt()

        conn.disconnect(receipt=None)

        self.assertTrue(listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assertTrue(listener.messages == 1, 'should have received 1 message')
        self.assertTrue(listener.errors == 0, 'should not have received any errors')
