import unittest

import pytest

import stomp
from stomp.listener import TestListener
from .testutils import *


@pytest.fixture()
def conn():
    conn = stomp.Connection11(get_artemis_host())
    conn.set_listener("testlistener", TestListener("123", print_to_log=True))
    conn.connect(get_artemis_user(), get_artemis_password(), wait=True)
    yield conn
    conn.disconnect(receipt=None)


class TestArtemis(object):

    def test_send_to_artemis(self, conn):
        conn.subscribe(destination="/queue/test", id=1, ack="auto")

        conn.send(body="this is a test", destination="/queue/test", receipt="123")

        validate_send(conn)