import pytest

import stomp
from stomp.listener import CombinedListener
from .testutils import *


@pytest.fixture()
def conn():
    conn = stomp.Connection10(get_stompserver_host())
    conn.set_listener('testlistener', CombinedListener('123', print_to_log=True))
    conn.connect(wait=True)
    yield conn
    conn.disconnect(receipt=None)


class TestStompServer(object):
    def test_send(self, conn):
        conn.subscribe(destination='/queue/test', id=1, ack='auto')

        conn.send(body='this is a test', destination='/queue/test', receipt='123')

        validate_send(conn)