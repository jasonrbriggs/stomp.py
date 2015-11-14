# -*- coding: UTF-8 -*-



import time
import unittest

import base64

import stomp

from testutils import TestListener, TestStompServer

class TestNonAsciiSend(unittest.TestCase):

    def setUp(self):
        conn = stomp.Connection([('127.0.0.2', 61613), ('localhost', 61613)], 'admin', 'password')
        listener = TestListener()
        conn.set_listener('', listener)
        conn.start()
        conn.connect(wait=True)
        self.conn = conn
        self.listener = listener
        
    def tearDown(self):
        if self.conn:
            self.conn.disconnect()
       
    def test_send_nonascii(self):
        self.conn.subscribe(destination='/queue/test', ack='auto', id="1")

        txt = u'марко'
        self.conn.send(txt, destination='/queue/test')

        time.sleep(3)

        self.assert_(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assert_(self.listener.messages == 1, 'should have received 1 message')
        self.assert_(self.listener.errors == 0, 'should not have received any errors')

        msg = self.listener.message_list[0]
        self.assertEquals(txt, msg.decode('utf-8'))
        
