import pytest

import stomp
from stomp.listener import TestListener, WaitingListener
from .testutils import *


@pytest.fixture()
def conn():
    conn = stomp.Connection11(get_rabbitmq_host())
    listener = TestListener("123", print_to_log=True)
    listener2 = WaitingListener("456")
    conn.set_listener("123", listener)
    conn.set_listener("456", listener2)
    conn.connect(get_rabbitmq_user(), get_rabbitmq_password(), wait=True)
    yield conn


class TestRabbitMQSend(object):

    def test_send(self, conn):
        listener = conn.get_listener("123")
        listener2 = conn.get_listener("456")

        queue_name = "/queue/test-%s" % listener.timestamp
        conn.subscribe(destination=queue_name, id=1, ack="auto")
        conn.send(body="this is a test", destination=queue_name, receipt="123")
        listener.wait_on_receipt()

        conn.disconnect(receipt="456")
        listener2.wait_on_receipt()

        assert listener.connections == 1, "should have received 1 connection acknowledgement"
        assert listener.messages == 1, "should have received 1 message"
        assert listener.errors == 0, "should not have received any errors"
        assert listener.disconnects == 1, "should have received 1 disconnect, was %s" % listener.disconnects