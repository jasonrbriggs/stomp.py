import logging

import stomp
from stomp.listener import TestListener
from .testutils import *


class BrokenConnectionListener(TestListener):
    def __init__(self, connection=None):
        TestListener.__init__(self)
        self.connection = connection
        self.messages_started = 0
        self.messages_completed = 0

    def on_error(self, frame):
        TestListener.on_error(self, frame)
        assert frame.body.startswith("org.apache.activemq.transport.stomp.ProtocolException: Not connected")

    def on_message(self, frame):
        TestListener.on_message(self, frame)
        self.messages_started += 1

        if self.connection.is_connected():
            try:
                self.connection.ack(frame.headers["message-id"], frame.headers["subscription"])
                self.messages_completed += 1
            except BrokenPipeError:
                logging.error("Expected BrokenPipeError")
                self.errors += 1


def conn():
    c = stomp.Connection11(get_default_host(), try_loopback_connect=False)
    c.set_listener("testlistener", BrokenConnectionListener(c))
    c.connect(get_default_user(), get_default_password(), wait=True)
    return c


def run_race_condition_situation(conn, wait):
    # happens when using ack mode "client-individual"
    # some load, eg > 50 messages received at same time (simulated with transaction)
    listener = conn.get_listener("testlistener")  # type: BrokenConnectionListener

    queuename = "/queue/disconnectmidack-%s" % listener.timestamp
    conn.subscribe(destination=queuename, id=1, ack="client-individual")

    trans_id = conn.begin()
    for i in range(50):
        conn.send(body="test message", destination=queuename, transaction=trans_id)
    conn.commit(transaction=trans_id)

    listener.wait_for_message()
    conn.disconnect(wait=wait)

    # wait for some messages to start between the time of disconnect start and finish (when the race condition happens)
    # needed to check result of listener.errors
    time.sleep(0.5)

    # return listener for asserts
    return listener


def assert_race_condition_disconnect_mid_ack(conn, wait=False):
    listener = run_race_condition_situation(conn, wait)

    started = listener.messages_started
    logging.debug("messages started %d", started)

    assert listener.connections == 1, "should have received 1 connection acknowledgement"
    assert listener.messages == started, f"should have received {started} message"

    # Causes either BrokenPipeError or ProtocolException: Not connected
    assert listener.errors >= 1, "should have at least one error"
    assert listener.messages_started > listener.messages_completed, f"should have not completed all started"


def assert_no_race_condition_disconnect_mid_ack(conn, wait=False):
    listener = run_race_condition_situation(conn, wait)

    started = listener.messages_started
    logging.debug("T%s : messages started %d", started, threading.get_native_id())

    assert listener.connections == 1, "should have received 1 connection acknowledgement"
    assert listener.messages == started, f"should have received {started} message"

    assert listener.errors == 0, "should not have errors"
    assert listener.messages_started == listener.messages_completed, f"should have completed all started"


def test_assert_race_condition_in_disconnect_mid_ack():
    found_race_condition = False
    retries_until_race_condition = 0
    while not found_race_condition:
        try:
            assert_race_condition_disconnect_mid_ack(conn())
            found_race_condition = True
        except AssertionError as e:
            retries_until_race_condition += 1
            continue

    assert found_race_condition is True
    # might occur at first try, might take 50 retries
    logging.warning("Tries until race condition: %d", retries_until_race_condition)


def test_assert_fixed_race_condition_in_disconnect_mid_ack():
    # same test case but asserts no error
    # you can increase forever, it always passes
    for n in range(100):
        assert_no_race_condition_disconnect_mid_ack(conn(), wait=True)
