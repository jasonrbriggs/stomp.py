import pytest

import stomp
from stomp import logging


@pytest.fixture
def stomp_transport():
    transport = stomp.transport.BaseTransport()
    yield transport


class TestTransport(object):
    def test_process_frame_unknown_command_empty_body(self, stomp_transport):
        fr = stomp.utils.Frame('test', {}, None)
        stomp_transport.process_frame(fr, None)

    def test_process_frame_empty_body(self, stomp_transport):
        logging.setLevel(logging.INFO)
        fr = stomp.utils.Frame('error', {}, None)
        stomp_transport.process_frame(fr, None)

    def test_process_frame_unknown_command(self, stomp_transport):
        fr = stomp.utils.Frame('test', {}, 'test message')
        stomp_transport.process_frame(fr, None)

    def test_process_frame(self, stomp_transport):
        logging.setLevel(logging.INFO)
        fr = stomp.utils.Frame('error', {}, 'test message')
        stomp_transport.process_frame(fr, None)
