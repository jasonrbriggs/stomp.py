import unittest

import stomp
from stomp.listener import WaitingListener
from stomp.test.testutils import *


class TestArtemisSend(unittest.TestCase):

    def setUp(self):
        pass

    def testbasic(self):
        conn = stomp.Connection11(get_artemis_host())
        listener = WaitingListener('123')
        conn.set_listener('', listener)
        conn.connect(get_artemis_user(), get_artemis_password(), wait=True)
        conn.subscribe(destination='/queue/test', id=1, ack='auto')

        conn.send(body='this is a test', destination='/queue/test', receipt='123')

        listener.wait_on_receipt()

        conn.disconnect(receipt=None)
