import os
import time

import pytest

import stomp
from stomp.listener import TestListener
from .testutils import *

import logging


@pytest.fixture()
def conn():
    if not is_inside_travis():
        conn = stomp.Connection11(get_ipv6_host())
        conn.set_listener("testlistener", TestListener("123", print_to_log=True))
        conn.connect("admin", "password", wait=True)
        yield conn
        conn.disconnect(receipt=None)
    else:
        yield None


class TestIP6(object):
    def test_ipv6_send(self, conn):
        if not is_inside_travis():
            logging.info("Running ipv6 test")
            timestamp = time.strftime("%Y%m%d%H%M%S")
            queuename = "/queue/testipv6-%s" % timestamp
            conn.subscribe(destination=queuename, id=1, ack="auto")

            conn.send(body="this is a test", destination=queuename, receipt="123")

            validate_send(conn)
