import unittest

from stomp.utils import *
from stomp.backward import *

class TestUtils(unittest.TestCase):
    def test_returns_true_when_localhost(self):
        self.assertEquals(1, is_localhost(('localhost', 8000)))
        self.assertEquals(1, is_localhost(('127.0.0.1', 8000)))
        self.assertEquals(2, is_localhost(('192.168.1.92', 8000)))

    def test_convert_frame_to_lines(self):
        f = Frame('SEND', {'header1' : 'value1', 'headerNone': None}, 'this is the body')

        lines = convert_frame_to_lines(f)

        s = pack(lines)

        if sys.hexversion >= 0x03000000:
            self.assertEquals(bytearray('SEND\nheader1:value1\n\nthis is the body\x00', 'ascii'), s)
        else:
            self.assertEquals('SEND\nheader1:value1\n\nthis is the body\x00', s)

    def test_parse_headers(self):
        lines = [
            r'h1:foo\c\\bar  ',
            r'h1:2nd h1 ignored -- not a must, but allowed and that is how we behave ATM',
            r'h\c2:baz\r\nquux',
        ]
        self.assertEquals(
            {'h1': r'foo:\bar  ', 'h:2': 'baz\r\nquux'}, parse_headers(lines))

    def test_calculate_heartbeats(self):
        chb = (3000, 5000)
        shb = map(str, reversed(chb))
        self.assertEquals((3000, 5000), calculate_heartbeats(shb, chb))
        shb = ('6000', '2000')
        self.assertEquals((3000, 6000), calculate_heartbeats(shb, chb))
        shb = ('0', '0')
        self.assertEquals((0, 0), calculate_heartbeats(shb, chb))
        shb = ('10000', '0')
        self.assertEquals((0, 10000), calculate_heartbeats(shb, chb))
        chb = (0, 0)
        self.assertEquals((0, 0), calculate_heartbeats(shb, chb))
