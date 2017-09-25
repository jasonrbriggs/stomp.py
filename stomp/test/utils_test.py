import unittest

from stomp.backward import *
from stomp.utils import *


class TestUtils(unittest.TestCase):
    def test_returns_true_when_localhost(self):
        self.assertEqual(1, is_localhost(('localhost', 8000)))
        self.assertEqual(1, is_localhost(('127.0.0.1', 8000)))
        self.assertEqual(2, is_localhost(('192.168.1.92', 8000)))

    def test_convert_frame_to_lines(self):
        f = Frame('SEND', {
            'header1': 'value1',
            'headerNone': None,
            ' no ': ' trimming ',
        }, 'this is the body')

        lines = convert_frame_to_lines(f)

        s = pack(lines)

        if sys.hexversion >= 0x03000000:
            self.assertEqual(bytearray('SEND\n no : trimming \nheader1:value1\n\nthis is the body\x00', 'ascii'), s)
        else:
            self.assertEqual('SEND\n no : trimming \nheader1:value1\n\nthis is the body\x00', s)

    def test_parse_headers(self):
        lines = [
            r'h1:foo\c\\bar  ',
            r'h1:2nd h1 ignored -- not a must, but allowed and that is how we behave ATM',
            r'h\c2:baz\r\nquux',
            r'h3:\\n\\c',
            r'against-spec:\t',  # should actually raise or something, we're against spec here ATM
            r' foo : bar',
        ]
        self.assertEqual({
            'h1': r'foo:\bar  ',
            'h:2': 'baz\r\nquux',
            'h3': r'\n\c',
            'against-spec': r'\t',
            ' foo ': ' bar',
        }, parse_headers(lines))

    def test_calculate_heartbeats(self):
        chb = (3000, 5000)
        shb = map(str, reversed(chb))
        self.assertEqual((3000, 5000), calculate_heartbeats(shb, chb))
        shb = ('6000', '2000')
        self.assertEqual((3000, 6000), calculate_heartbeats(shb, chb))
        shb = ('0', '0')
        self.assertEqual((0, 0), calculate_heartbeats(shb, chb))
        shb = ('10000', '0')
        self.assertEqual((0, 10000), calculate_heartbeats(shb, chb))
        chb = (0, 0)
        self.assertEqual((0, 0), calculate_heartbeats(shb, chb))

    def test_parse_frame(self):
        # heartbeat
        f = parse_frame(b'\x0a')
        self.assertEqual(str(f), str(Frame('heartbeat')))
        # oddball/broken
        f = parse_frame(b'FOO')
        self.assertEqual(str(f), str(Frame('FOO', body=b'')))
        # empty body
        f = parse_frame(b'RECEIPT\nreceipt-id:message-12345\n\n')
        self.assertEqual(str(f), str(Frame('RECEIPT', {'receipt-id': 'message-12345'}, b'')))
        # no headers
        f = parse_frame(b'ERROR\n\n')
        self.assertEqual(str(f), str(Frame('ERROR', body=b'')))
        # regular, different linefeeds
        for lf in b'\n', b'\r\n':
            f = parse_frame(
                b'MESSAGE' + lf +
                b'content-type:text/plain' + lf +
                lf +
                b'hello world!'
            )
            self.assertEqual(str(f), str(Frame('MESSAGE', {'content-type': 'text/plain'}, b'hello world!')))

    def test_clean_default_headers(self):
        Frame().headers['foo'] = 'bar'
        self.assertEqual(Frame().headers, {})
