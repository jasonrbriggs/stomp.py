import unittest

from stomp.utils import *
from stomp.backward import *

class TestUtils(unittest.TestCase):
    def test_returns_true_when_localhost(self):
        self.assertEquals(1, is_localhost(('localhost', 8000)))
        self.assertEquals(1, is_localhost(('127.0.0.1', 8000)))
        self.assertEquals(2, is_localhost(('192.168.1.92', 8000)))

    def test_convert_frame_to_lines(self):
        f = Frame('SEND', { 'header1' : 'value1'}, 'this is the body')

        lines = convert_frame_to_lines(f)

        s = pack(lines)

        if sys.hexversion >= 0x03000000:
            self.assertEquals(bytearray('SEND\nheader1:value1\n\nthis is the body\x00', 'ascii'), s)
        else:
            self.assertEquals('SEND\nheader1:value1\n\nthis is the body\x00', s)