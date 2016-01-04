import unittest

from stomp import backward3


class TestBackward3(unittest.TestCase):
    def test_pack_mixed_string_and_bytes(self):
        lines = ['SEND', '\n', 'header1:test', '\u6771']
        self.assertEqual(backward3.encode(backward3.pack(lines)),
                         b'SEND\nheader1:test\xe6\x9d\xb1')
        lines = ['SEND', '\n', 'header1:test', b'\xe6\x9d\xb1']
        self.assertEqual(backward3.encode(backward3.pack(lines)),
                         b'SEND\nheader1:test\xe6\x9d\xb1')

    def test_decode(self):
        self.assertTrue(backward3.decode(None) is None)
        self.assertEqual('test', backward3.decode(b'test'))

    def test_encode(self):
        self.assertEqual(b'test', backward3.encode('test'))
        self.assertEqual(b'test', backward3.encode(b'test'))
        self.assertRaises(TypeError, backward3.encode, None)
