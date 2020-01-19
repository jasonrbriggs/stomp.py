import unittest

import pytest

import stomp
from stomp.listener import TestListener
from .testutils import *


@pytest.fixture()
def conn():
    conn = stomp.Connection11(get_default_host())
    conn.set_listener("testlistener", TestListener("123", print_to_log=True))
    conn.connect(get_default_user(), get_default_password(), wait=True)
    yield conn
    conn.disconnect(receipt=None)


class TestActiveMQ(object):

    def test_send_to_activemq(self, conn):
        conn.subscribe(destination="/queue/test", id=1, ack="auto")

        conn.send(body="this is a test", destination="/queue/test", receipt="123")

        validate_send(conn)