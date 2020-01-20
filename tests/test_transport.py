import pytest

import stomp
from stomp import logging


@pytest.fixture
def stomp_transport():
    transport = stomp.transport.BaseTransport()
    yield transport


class TestTransport(object):
    def test_should_reject_null_listener(self, stomp_transport):
        with pytest.raises(AssertionError):
            stomp_transport.set_listener("testlistener", None)

    def test_process_frame_unknown_command_empty_body(self, stomp_transport):
        fr = stomp.utils.Frame("test", {}, None)
        stomp_transport.process_frame(fr, None)

    def test_process_frame_empty_body(self, stomp_transport):
        logging.setLevel(logging.INFO)
        fr = stomp.utils.Frame("error", {}, None)
        stomp_transport.process_frame(fr, None)

    def test_process_frame_unknown_command(self, stomp_transport):
        fr = stomp.utils.Frame("test", {}, "test message")
        stomp_transport.process_frame(fr, None)

    def test_process_frame(self, stomp_transport):
        logging.setLevel(logging.INFO)
        fr = stomp.utils.Frame("error", {}, "test message")
        stomp_transport.process_frame(fr, None)

    # just for coverage
    def test_methods_for_coverage(self, stomp_transport):
        stomp_transport.send(None)
        stomp_transport.receive()
        stomp_transport.cleanup()
        stomp_transport.attempt_connection()
        stomp_transport.disconnect_socket()

