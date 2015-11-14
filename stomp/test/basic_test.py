import time
import unittest

import stomp
from stomp import exception

from testutils import TestListener, TestStompServer


class TestBasicSend(unittest.TestCase):

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
       
    def testbasic(self):
        self.conn.subscribe(destination='/queue/test', ack='auto')

        self.conn.send('this is a test', destination='/queue/test')

        time.sleep(3)

        self.assert_(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assert_(self.listener.messages == 1, 'should have received 1 message')
        self.assert_(self.listener.errors == 0, 'should not have received any errors')
    
    def testcommit(self):
        self.conn.subscribe(destination='/queue/test', ack='auto')
        trans_id = self.conn.begin()
        self.conn.send('this is a test1', destination='/queue/test', transaction=trans_id)
        self.conn.send('this is a test2', destination='/queue/test', transaction=trans_id)
        self.conn.send('this is a test3', destination='/queue/test', transaction=trans_id)

        time.sleep(3)

        self.assert_(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assert_(self.listener.messages == 0, 'should not have received any messages')

        self.conn.commit(transaction = trans_id)
        time.sleep(3)

        self.assert_(self.listener.messages == 3, 'should have received 3 messages')
        self.assert_(self.listener.errors == 0, 'should not have received any errors')

    def testabort(self):
        self.conn.subscribe(destination='/queue/test', ack='auto')
        trans_id = self.conn.begin()
        self.conn.send('this is a test1', destination='/queue/test', transaction=trans_id)
        self.conn.send('this is a test2', destination='/queue/test', transaction=trans_id)
        self.conn.send('this is a test3', destination='/queue/test', transaction=trans_id)

        time.sleep(3)

        self.assert_(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assert_(self.listener.messages == 0, 'should not have received any messages')

        self.conn.abort(transaction = trans_id)
        time.sleep(3)

        self.assert_(self.listener.messages == 0, 'should not have received any messages')
        self.assert_(self.listener.errors == 0, 'should not have received any errors')
        
    def testtimeout(self):
        conn = stomp.Connection([('127.0.0.2', 60000)], timeout=5, reconnect_attempts_max=1)
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
            conn = stomp.Connection([('127.0.0.1', 61614), ('localhost', 61614)], 'admin', 'password', use_ssl = True)
            conn.set_listener('', self.listener)
            conn.start()
            conn.connect(wait=True)
            conn.subscribe(destination='/queue/test', ack='auto')

            conn.send('this is a test', destination='/queue/test')

            time.sleep(3)
            conn.disconnect()

            self.assert_(self.listener.connections > 1, 'should have received 1 connection acknowledgement')
            self.assert_(self.listener.messages == 1, 'should have received 1 message')
            self.assert_(self.listener.errors == 0, 'should not have received any errors')
        except:
            pass

