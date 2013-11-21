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
        self.timestamp = time.strftime('%Y%m%d%H%M%S')
        
    def tearDown(self):
        if self.conn:
            self.conn.disconnect()
       
    def test_send_nonascii(self):
        queuename = '/queue/p3nonasciitest-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, ack='auto', id='1')

        txt = 'марко'
        self.conn.send(body=txt, destination=queuename, receipt='123')

        self.listener.wait_on_receipt()

        self.assert_(self.listener.connections >= 1, 'should have received 1 connection acknowledgement')
        self.assert_(self.listener.messages >= 1, 'should have received 1 message')
        self.assert_(self.listener.errors == 0, 'should not have received any errors')
        
        (headers, msg) = self.listener.get_latest_message()
        self.assertEquals(txt, msg)