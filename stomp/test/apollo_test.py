import unittest

import stomp
from stomp.listener import WaitingListener
from stomp.test.testutils import *


class TestApolloSend(unittest.TestCase):

    def setUp(self):
        pass

    def testbasic(self):
        conn = stomp.Connection11(get_apollo_host())
        listener = WaitingListener('123')
        conn.set_listener('', listener)
        conn.connect(get_default_user(), get_default_password(), wait=True)
        conn.subscribe(destination='/queue/test', id=1, ack='auto')

        conn.send(body='this is a test', destination='/queue/test', receipt='123')

        listener.wait_on_receipt()

        conn.disconnect(receipt=None)
