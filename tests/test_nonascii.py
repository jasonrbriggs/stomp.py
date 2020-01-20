# -*- coding: UTF-8 -*-

import filecmp
import time

import pytest

import stomp
from stomp.listener import *
from .testutils import *


@pytest.fixture
def conn():
    conn = stomp.Connection(get_default_host(), auto_decode=False)
    listener = TestListener("123", print_to_log=True)
    conn.set_listener("testlistener", listener)
    conn.connect(get_default_user(), get_default_password(), wait=True)
    yield conn
    conn.disconnect(receipt=None)

@pytest.fixture
def conn_encode():
    conn = stomp.Connection(get_default_host(), auto_decode=True)
    listener = TestListener("123", print_to_log=True)
    conn.set_listener("testlistener", listener)
    conn.connect(get_default_user(), get_default_password(), wait=True)
    yield conn
    conn.disconnect(receipt=None)


@pytest.fixture
def conn_encode_utf18():
    conn = stomp.Connection(get_default_host(), auto_decode=True, encoding="utf-16")
    listener = TestListener("123", print_to_log=True)
    conn.set_listener("testlistener", listener)
    conn.connect(get_default_user(), get_default_password(), wait=True)
    yield conn
    conn.disconnect(receipt=None)


class TestNonAsciiSend(object):

    def test_send_nonascii(self, conn):
        listener = conn.get_listener("testlistener")
        queuename = "/queue/nonasciitest-%s" % listener.timestamp
        conn.subscribe(destination=queuename, ack="auto", id="1")

        txt = test_text_for_utf8
        conn.send(body=txt, destination=queuename, receipt="123")

        listener.wait_for_message()

        assert listener.connections >= 1, "should have received 1 connection acknowledgement"
        assert listener.messages >= 1, "should have received 1 message"
        assert listener.errors == 0, "should not have received any errors"

        (_, msg) = listener.get_latest_message()
        assert encode(txt) == msg

    def test_image_send(self, conn):
        d = os.path.dirname(os.path.realpath(__file__))
        srcname = os.path.join(d, "test.gif")
        with open(srcname, 'rb') as f:
            img = f.read()

        listener = conn.get_listener("testlistener")
        queuename = "/queue/nonascii-image-%s" % listener.timestamp
        conn.subscribe(destination=queuename, ack="auto", id="1")

        conn.send(body=img, destination=queuename, receipt="123")

        listener.wait_for_message()

        assert listener.connections >= 1, "should have received 1 connection acknowledgement"
        assert listener.messages >= 1, "should have received 1 message"
        assert listener.errors == 0, "should not have received any errors"

        (_, msg) = listener.get_latest_message()
        assert img == msg
        destname = os.path.join(d, "test-out.gif")
        with open(destname, 'wb') as f:
            f.write(img)

        assert filecmp.cmp(srcname, destname)

    def test_image_send(self, conn):
        d = os.path.dirname(os.path.realpath(__file__))
        srcname = os.path.join(d, "test.gif.gz")
        with open(srcname, 'rb') as f:
            img = f.read()

        listener = conn.get_listener("testlistener")
        queuename = "/queue/nonascii-image-%s" % listener.timestamp
        conn.subscribe(destination=queuename, ack="auto", id="1")

        conn.send(body=img, destination=queuename, receipt="123")

        listener.wait_for_message()

        assert listener.connections >= 1, "should have received 1 connection acknowledgement"
        assert listener.messages >= 1, "should have received 1 message"
        assert listener.errors == 0, "should not have received any errors"

        (_, msg) = listener.get_latest_message()
        assert img == msg
        destname = os.path.join(d, "test-out.gif.gz")
        with open(destname, 'wb') as f:
            f.write(img)

        assert filecmp.cmp(srcname, destname)


class TestNonAsciiSendAutoDecode(object):

    def test_send_nonascii_auto_decoding(self, conn_encode):
        listener = conn_encode.get_listener("testlistener")
        queuename = "/queue/nonasciitest2-%s" % listener.timestamp
        conn_encode.subscribe(destination=queuename, ack="auto", id="1")

        txt = test_text_for_utf8
        conn_encode.send(body=txt, destination=queuename, receipt="123")

        listener.wait_for_message()

        assert listener.connections >= 1, "should have received 1 connection acknowledgement"
        assert listener.messages >= 1, "should have received 1 message"
        assert listener.errors == 0, "should not have received any errors"

        (_, msg) = listener.get_latest_message()

        assert txt == msg


class TestNonAsciiSendSpecificEncoding(object):

    def test_send_nonascii_auto_encoding(self, conn_encode_utf18):
        listener = conn_encode_utf18.get_listener("testlistener")
        queuename = "/queue/nonasciitest2-%s" % listener.timestamp
        conn_encode_utf18.subscribe(destination=queuename, ack="auto", id="1")

        txt = test_text_for_utf16
        conn_encode_utf18.send(body=txt, destination=queuename, receipt="123")

        listener.wait_for_message()

        assert listener.connections >= 1, "should have received 1 connection acknowledgement"
        assert listener.messages >= 1, "should have received 1 message"
        assert listener.errors == 0, "should not have received any errors"

        (_, msg) = listener.get_latest_message()

        assert txt == msg
