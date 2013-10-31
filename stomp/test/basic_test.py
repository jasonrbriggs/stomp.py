import os
import signal
import time
import unittest

import stomp
from stomp import exception

from testutils import *


class TestBasicSend(unittest.TestCase):

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
       
    def testbasic(self):
        self.conn.subscribe(destination='/queue/test', id=1, ack='auto')

        self.conn.send(body='this is a test', destination='/queue/test', receipt='123')

        self.listener.wait_on_receipt()

        self.assert_(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assert_(self.listener.messages == 1, 'should have received 1 message')
        self.assert_(self.listener.errors == 0, 'should not have received any errors')
    
    def testcommit(self):
        self.conn.subscribe(destination='/queue/test', id=1, ack='auto')
        trans_id = self.conn.begin()
        self.conn.send(body='this is a test1', destination='/queue/test', transaction=trans_id)
        self.conn.send(body='this is a test2', destination='/queue/test', transaction=trans_id)
        self.conn.send(body='this is a test3', destination='/queue/test', transaction=trans_id, receipt='123')

        time.sleep(3)

        self.assert_(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assert_(self.listener.messages == 0, 'should not have received any messages')

        self.conn.commit(transaction = trans_id)
        self.listener.wait_on_receipt()

        self.assert_(self.listener.messages == 3, 'should have received 3 messages')
        self.assert_(self.listener.errors == 0, 'should not have received any errors')

    def testabort(self):
        self.conn.subscribe(destination='/queue/test', id=1, ack='auto')
        trans_id = self.conn.begin()
        self.conn.send(body='this is a test1', destination='/queue/test', transaction=trans_id)
        self.conn.send(body='this is a test2', destination='/queue/test', transaction=trans_id)
        self.conn.send(body='this is a test3', destination='/queue/test', transaction=trans_id)

        time.sleep(3)

        self.assert_(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assert_(self.listener.messages == 0, 'should not have received any messages')

        self.conn.abort(transaction = trans_id)
        time.sleep(3)

        self.assert_(self.listener.messages == 0, 'should not have received any messages')
        self.assert_(self.listener.errors == 0, 'should not have received any errors')
      
    def testtimeout(self):
        conn = stomp.Connection([('203.0.113.100', 60000)], timeout=5, reconnect_attempts_max=1)
        conn.set_listener('', self.listener)
        
        try:
            ms = time.time()
            conn.start()
            self.fail("shouldn't happen")
        except exception.ConnectFailedException:
            pass # success!
            ms = time.time() - ms
            self.assert_(ms > 5.0, 'connection timeout should have been at least 5 seconds')

    def testssl(self):
        try:
            import ssl
            conn = stomp.Connection(get_standard_ssl_host(), use_ssl = True)
            conn.set_listener('', self.listener)
            conn.start()
            conn.connect('admin', 'password', wait=True)
            conn.subscribe(destination='/queue/test', id=1, ack='auto')

            conn.send(body='this is a test', destination='/queue/test', receipt='123')

            self.listener.wait_on_receipt()
            conn.disconnect()

            self.assert_(self.listener.connections > 1, 'should have received 1 connection acknowledgement')
            self.assert_(self.listener.messages == 1, 'should have received 1 message')
            self.assert_(self.listener.errors == 0, 'should not have received any errors')
        except:
            pass

    def testchildinterrupt(self):
        def childhandler(signum, frame):
            print("received child signal")
 
        oldhandler = signal.signal(signal.SIGCHLD, childhandler)
 
        self.conn.subscribe(destination='/queue/test', id=1, ack='auto', receipt='123')
 
        self.listener.wait_on_receipt()
 
        self.conn.send(body='this is an interrupt test 1', destination='/queue/test')
 
        print("causing signal by starting child process")
        os.system("sleep 1")
 
        time.sleep(1)
 
        signal.signal(signal.SIGCHLD, oldhandler)
        print("completed signal section")
 
        self.conn.send(body='this is an interrupt test 2', destination='/queue/test', receipt='123')
 
        self.listener.wait_on_receipt()
 
        self.assert_(self.listener.connections == 1, 'should have received 1 connection acknowledgment')
        self.assert_(self.listener.errors == 0, 'should not have received any errors')
        self.assert_(self.conn.is_connected(), 'should still be connected to STOMP provider')
