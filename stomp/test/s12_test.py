import os
import signal
import time
import unittest

import stomp
from stomp import exception

from testutils import *


class Test12Connect(unittest.TestCase):

    def setUp(self):
        conn = stomp.Connection12(get_standard_host())
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
       
    def testsend12(self):
        queuename = '/queue/testsend12-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='auto')

        self.conn.send(body='this is a test using protocol 1.2', destination=queuename, receipt='123')

        self.listener.wait_on_receipt()

        self.assert_(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assert_(self.listener.messages == 1, 'should have received 1 message')
        self.assert_(self.listener.errors == 0, 'should not have received any errors')
        
    def testclientack12(self):
        queuename = '/queue/testclientack12-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='client-individual')

        self.conn.send(body='this is a test', destination=queuename, receipt='123')

        self.listener.wait_for_message()
        
        (headers, msg) = self.listener.get_latest_message()
        
        ack_id = headers['ack']
        
        self.conn.ack(ack_id)

    def testclientnack12(self):
        queuename = '/queue/testclientnack12-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='client-individual')

        self.conn.send(body='this is a test', destination=queuename, receipt='123')

        self.listener.wait_for_message()
        
        (headers, msg) = self.listener.get_latest_message()
        
        ack_id = headers['ack']
        
        self.conn.nack(ack_id)
