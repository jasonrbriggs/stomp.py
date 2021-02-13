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


@pytest.fixture()
def conn2():
    conn2 = stomp.Connection11(get_artemis_host())
    conn2.set_listener("testlistener", TestListener("456", print_to_log=True))
    conn2.connect(get_artemis_user(), get_artemis_password(), wait=True, headers={'consumerWindowSize': 0})
    yield conn2
    conn2.disconnect(receipt=None)


class TestArtemis(object):

    def test_send_to_artemis(self, conn):
        conn.subscribe(destination="/queue/test", id=1, ack="auto")

        conn.send(body="this is a test", destination="/queue/test", receipt="123")

        validate_send(conn)

    def test_prefetchsize(self, conn2):
        conn2.subscribe(destination="/queue/test2", id=2, ack="auto", headers={'consumerWindowSize': 0})

        conn2.send(body="testing sending a message after subscribing with prefetch",
                   destination="/queue/test2", receipt="456")

        validate_send(conn2)
