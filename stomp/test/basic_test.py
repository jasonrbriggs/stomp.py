import os
import signal
import time
import unittest

import stomp
from stomp import exception
from stomp.backward import monotonic
from stomp.listener import TestListener
from stomp.test.testutils import *


class TestBasicSend(unittest.TestCase):

    def setUp(self):
        conn = stomp.Connection(get_default_host())
        listener = TestListener('123')
        conn.set_listener('', listener)
        conn.start()
        conn.connect(get_default_user(), get_default_password(), wait=True)
        self.conn = conn
        self.listener = listener
        self.timestamp = time.strftime('%Y%m%d%H%M%S')

    def tearDown(self):
        if self.conn:
            self.conn.disconnect(receipt=None)

    def test_basic(self):
        queuename = '/queue/test1-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='auto')

        self.conn.send(body='this is a test', destination=queuename, receipt='123')

        self.listener.wait_for_message()

        self.assertTrue(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assertTrue(self.listener.messages == 1, 'should have received 1 message')
        self.assertTrue(self.listener.errors == 0, 'should not have received any errors')

    def test_commit(self):
        queuename = '/queue/test2-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='auto')
        trans_id = self.conn.begin()
        self.conn.send(body='this is a test1', destination=queuename, transaction=trans_id)
        self.conn.send(body='this is a test2', destination=queuename, transaction=trans_id)
        self.conn.send(body='this is a test3', destination=queuename, transaction=trans_id, receipt='123')

        time.sleep(3)

        self.assertTrue(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assertTrue(self.listener.messages == 0, 'should not have received any messages')

        self.conn.commit(transaction=trans_id)
        self.listener.wait_for_message()
        time.sleep(3)

        self.assertTrue(self.listener.messages == 3, 'should have received 3 messages')
        self.assertTrue(self.listener.errors == 0, 'should not have received any errors')

    def test_abort(self):
        queuename = '/queue/test3-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='auto')
        trans_id = self.conn.begin()
        self.conn.send(body='this is a test1', destination=queuename, transaction=trans_id)
        self.conn.send(body='this is a test2', destination=queuename, transaction=trans_id)
        self.conn.send(body='this is a test3', destination=queuename, transaction=trans_id)

        time.sleep(3)

        self.assertTrue(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assertTrue(self.listener.messages == 0, 'should not have received any messages')

        self.conn.abort(transaction=trans_id)
        time.sleep(3)

        self.assertTrue(self.listener.messages == 0, 'should not have received any messages')
        self.assertTrue(self.listener.errors == 0, 'should not have received any errors')

    def test_timeout(self):
        conn = stomp.Connection([('192.0.2.0', 60000)], timeout=5, reconnect_attempts_max=1)
        conn.set_listener('', self.listener)

        try:
            ms = monotonic()
            conn.start()
            self.fail("shouldn't happen")
        except exception.ConnectFailedException:
            pass  # success!
            ms = monotonic() - ms
            self.assertTrue(ms > 5.0, 'connection timeout should have been at least 5 seconds')

    def test_childinterrupt(self):
        def childhandler(signum, frame):
            print("received child signal")

        oldhandler = signal.signal(signal.SIGCHLD, childhandler)

        queuename = '/queue/test5-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='auto', receipt='123')

        self.listener.wait_on_receipt()

        self.conn.send(body='this is an interrupt test 1', destination=queuename)

        print("causing signal by starting child process")
        os.system("sleep 1")

        time.sleep(1)

        signal.signal(signal.SIGCHLD, oldhandler)
        print("completed signal section")

        self.conn.send(body='this is an interrupt test 2', destination=queuename, receipt='123')

        self.listener.wait_for_message()

        self.assertTrue(self.listener.connections == 1, 'should have received 1 connection acknowledgment')
        self.assertTrue(self.listener.errors == 0, 'should not have received any errors')
        self.assertTrue(self.conn.is_connected(), 'should still be connected to STOMP provider')

    def test_clientack(self):
        queuename = '/queue/testclientack-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='client')

        self.conn.send(body='this is a test', destination=queuename, receipt='123')

        self.listener.wait_for_message()

        (headers, _) = self.listener.get_latest_message()

        message_id = headers['message-id']
        subscription = headers['subscription']

        self.conn.ack(message_id, subscription)

    def test_clientnack(self):
        queuename = '/queue/testclientnack-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='client')

        self.conn.send(body='this is a test', destination=queuename, receipt='123')

        self.listener.wait_for_message()

        (headers, _) = self.listener.get_latest_message()

        message_id = headers['message-id']
        subscription = headers['subscription']

        self.conn.nack(message_id, subscription)

    def test_specialchars(self):
        queuename = '/queue/testspecialchars-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='client')

        hdrs = {
            'special-1': 'test with colon : test',
            'special-2': 'test with backslash \\ test',
            'special-3': 'test with newline \n'
        }

        self.conn.send(body='this is a test', headers=hdrs, destination=queuename, receipt='123')

        self.listener.wait_for_message()

        (headers, _) = self.listener.get_latest_message()

        _ = headers['message-id']
        _ = headers['subscription']
        self.assertTrue('special-1' in headers)
        self.assertEqual('test with colon : test', headers['special-1'])
        self.assertTrue('special-2' in headers)
        self.assertEqual('test with backslash \\ test', headers['special-2'])
        self.assertTrue('special-3' in headers)
        self.assertEqual('test with newline \n', headers['special-3'])


class TestConnectionErrors(unittest.TestCase):
    def test_connect_wait_error(self):
        conn = stomp.Connection(get_default_host())
        conn.start()
        try:
            conn.connect('invalid', 'user', True)
            self.fail("Shouldn't happen")
        except:
            pass

    def test_connect_nowait_error(self):
        conn = stomp.Connection(get_default_host())
        conn.start()
        try:
            conn.connect('invalid', 'user', False)
            self.assertFalse(conn.is_connected(), 'Should not be connected')
        except:
            self.fail("Shouldn't happen")
