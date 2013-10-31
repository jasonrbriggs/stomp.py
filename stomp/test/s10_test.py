import os
import signal
import time
import unittest

import stomp
from stomp import exception

from testutils import *


class Test10Connect(unittest.TestCase):

    def setUp(self):
        conn = stomp.Connection10(get_standard_host())
        listener = TestListener('123')
        conn.set_listener('', listener)
        conn.start()
        conn.connect('admin', 'password', wait=True)
        self.conn = conn
        self.listener = listener
        
    def tearDown(self):
        if self.conn:
            self.conn.disconnect()
       
    def testsend10(self):
        self.conn.subscribe(destination='/queue/test', ack='auto')

        self.conn.send(body='this is a test using protocol 1.0', destination='/queue/test', receipt='123')

        self.listener.wait_on_receipt()

        self.assert_(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assert_(self.listener.messages == 1, 'should have received 1 message')
        self.assert_(self.listener.errors == 0, 'should not have received any errors')