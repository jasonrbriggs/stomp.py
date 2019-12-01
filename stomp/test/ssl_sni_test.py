import unittest

import stomp
from stomp.listener import TestListener
from stomp.test.testutils import *


class TestSNIMQSend(unittest.TestCase):
    """
    To test SNI:

    - Start the docker container

    - Add a couple fully qualified hostnames to your /etc/hosts
        # SNI test hosts
        172.17.0.2 my.example.com
        172.17.0.2 my.example.org

    Connections with SNI to "my.example.com" will be routed to the STOMP server on port 62613.
    Connections without SNI won't be routed.

    """

    def setUp(self):
        pass

    def testconnect(self):
        conn = stomp.Connection11(get_sni_ssl_host())
        conn.set_ssl(get_sni_ssl_host())
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
