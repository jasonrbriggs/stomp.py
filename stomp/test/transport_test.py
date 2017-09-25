import logging
import unittest

import stomp


class TestTransport(unittest.TestCase):
    def setUp(self):
        self.transport = stomp.transport.BaseTransport()

    def test_process_frame_unknown_command_empty_body(self):
        fr = stomp.utils.Frame('test', {}, None)
        self.transport.process_frame(fr, None)

    def test_process_frame_empty_body(self):
        stomp.transport.log.setLevel(logging.INFO)
        fr = stomp.utils.Frame('error', {}, None)
        self.transport.process_frame(fr, None)

    def test_process_frame_unknown_command(self):
        fr = stomp.utils.Frame('test', {}, 'test message')
        self.transport.process_frame(fr, None)

    def test_process_frame(self):
        stomp.transport.log.setLevel(logging.INFO)
        fr = stomp.utils.Frame('error', {}, 'test message')
        self.transport.process_frame(fr, None)
