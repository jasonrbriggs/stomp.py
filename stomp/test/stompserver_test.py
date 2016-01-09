import unittest

import stomp
from stomp.listener import TestListener
from stomp.test.testutils import *


class TestStompServerSend(unittest.TestCase):

    def setUp(self):
        pass

    def testbasic(self):
        conn = stomp.Connection10(get_stompserver_host())
        listener = TestListener('123')
        conn.set_listener('', listener)
        conn.start()
        conn.connect(wait=True)
        conn.subscribe(destination='/queue/test', ack='auto')

        conn.send(body='this is a test', destination='/queue/test', receipt='123')

        listener.wait_on_receipt()

        conn.unsubscribe('/queue/test')

        conn.disconnect(receipt=None)

        self.assertTrue(listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assertTrue(listener.messages == 1, 'should have received 1 message')
        self.assertTrue(listener.errors == 0, 'should not have received any errors')
