# -*- coding: UTF-8 -*-

import time
import unittest

import stomp
from stomp.listener import TestListener
from stomp.test.testutils import *


class TestNonAsciiSend(unittest.TestCase):

    def setUp(self):
        conn = stomp.Connection(get_default_host(), auto_decode=False)
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

    def test_send_nonascii(self):
        queuename = '/queue/p3nonasciitest-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, ack='auto', id='1')

        txt = 'марко'
        self.conn.send(body=txt, destination=queuename, receipt='123')

        self.listener.wait_for_message()

        self.assertTrue(self.listener.connections >= 1, 'should have received 1 connection acknowledgement')
        self.assertTrue(self.listener.messages >= 1, 'should have received 1 message')
        self.assertTrue(self.listener.errors == 0, 'should not have received any errors')

        (_, msg) = self.listener.get_latest_message()
        self.assertEqual(stomp.backward.encode(txt), msg)

    def test_image_send(self):
        d = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(d, 'test.gif'), 'rb') as f:
            img = f.read()

        queuename = '/queue/p3nonascii-image-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, ack='auto', id='1')

        self.conn.send(body=img, destination=queuename, receipt='123')

        self.listener.wait_for_message()

        self.assertTrue(self.listener.connections >= 1, 'should have received 1 connection acknowledgement')
        self.assertTrue(self.listener.messages >= 1, 'should have received 1 message')
        self.assertTrue(self.listener.errors == 0, 'should not have received any errors')

        (_, msg) = self.listener.get_latest_message()
        self.assertEqual(img, msg)
        with open(os.path.join(d, 'test-out.gif'), 'wb') as f:
            f.write(img)


class TestNonAsciiSendAutoEncoding(unittest.TestCase):
    def setUp(self):
        conn = stomp.Connection(get_default_host(), auto_decode=True)
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

    def test_send_nonascii_auto_encoding(self):
        queuename = '/queue/p3nonasciitest2-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, ack='auto', id='1')

        txt = 'марко'
        self.conn.send(body=txt, destination=queuename, receipt='123')

        self.listener.wait_for_message()

        self.assertTrue(self.listener.connections >= 1, 'should have received 1 connection acknowledgement')
        self.assertTrue(self.listener.messages >= 1, 'should have received 1 message')
        self.assertTrue(self.listener.errors == 0, 'should not have received any errors')

        (_, msg) = self.listener.get_latest_message()
        self.assertEqual(txt, msg)
