import os
import time

import pytest

import stomp
from stomp.listener import TestListener
from stomp import logging
from .testutils import *


def is_inside_travis():
    logging.info(">>>>>>>>>>>>>>>> %s" % os.environ.get('TRAVIS', 'false'))
    if os.environ.get('TRAVIS', 'false') == 'true':
        logging.info("Not running ipv6 test inside travis")
        return True
    return False


@pytest.fixture()
def conn():
    conn = stomp.Connection11(get_ipv6_host())
    conn.set_listener('testlistener', TestListener('123', print_to_log=True))
    conn.connect('admin', 'password', wait=True)
    yield conn
    conn.disconnect(receipt=None)


class TestIP6(object):
    def test_ipv6_send(self, conn):
        if not is_inside_travis():
            logging.info("Running ipv6 test")
            timestamp = time.strftime('%Y%m%d%H%M%S')
            queuename = '/queue/testipv6-%s' % timestamp
            conn.subscribe(destination=queuename, id=1, ack='auto')

            conn.send(body='this is a test', destination=queuename, receipt='123')

            validate_send(conn)
