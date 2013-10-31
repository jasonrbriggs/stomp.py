# -*- coding: UTF-8 -*-

import time
import unittest

import stomp

from testutils import *

class TestNonAsciiSend(unittest.TestCase):

    def setUp(self):
        conn = stomp.Connection(get_standard_host())
        listener = TestListener('123')
        conn.set_listener('', listener)
        conn.start()
        conn.connect('admin', 'password', wait=True)
        self.conn = conn
        self.listener = listener
        
    def tearDown(self):
        if self.conn:
            self.conn.disconnect()
       
    def test_send_nonascii(self):
        self.conn.subscribe(destination='/queue/test', ack='auto', id='1')

        txt = 'марко'
        self.conn.send(body=txt, destination='/queue/test', receipt='123')

        self.listener.wait_on_receipt()

        self.assert_(self.listener.connections >= 1, 'should have received 1 connection acknowledgement')
        self.assert_(self.listener.messages >= 1, 'should have received 1 message')
        self.assert_(self.listener.errors == 0, 'should not have received any errors')
        
        msg = self.listener.message_list[0]
        self.assertEquals(txt, msg)