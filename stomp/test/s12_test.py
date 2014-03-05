import time
import unittest

import stomp
from stomp import exception

from stomp.test.testutils import *


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
            self.conn.disconnect(receipt=None)
       
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

    def testtimeout(self):
        server = TestStompServer('127.0.0.1', 60000)
        try:
            server.start()

            server.add_frame('''ERROR
message: connection failed\x00''')

            conn = stomp.Connection12([('127.0.0.1', 60000)])
            listener = TestListener()
            conn.set_listener('', listener)
            conn.start()
            try:
                conn.connect(wait=True)
                self.fail("shouldn't happen")
            except exception.ConnectFailedException:
                pass
        finally:
            server.stop()
            
    def test_specialchars12(self):
        queuename = '/queue/testspecialchars12-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='client')

        hdrs = {
            'special-1' : 'test with colon : test',
            'special-2' : 'test with backslash \\ test',
            'special-3' : 'test with newline \n',
            'special-4' : 'test with carriage return \r'
        }

        self.conn.send(body='this is a test', headers = hdrs, destination=queuename, receipt='123')

        self.listener.wait_on_receipt()
        
        (headers, msg) = self.listener.get_latest_message()
        
        message_id = headers['message-id']
        subscription = headers['subscription']
        self.assert_('special-1' in headers)
        self.assertEqual('test with colon : test', headers['special-1'])
        self.assert_('special-2' in headers)
        self.assertEqual('test with backslash \\ test', headers['special-2'])
        self.assert_('special-3' in headers)
        self.assertEqual('test with newline \n', headers['special-3'])
        self.assert_('special-4' in headers)
        self.assertEqual('test with carriage return \r', headers['special-4'])
