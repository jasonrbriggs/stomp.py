import unittest

from stomp import backward2


class TestBackward2(unittest.TestCase):
    def test_pack_mixed_string_and_bytes(self):
        lines = ['SEND', '\n', u'header1:test', u'\u6771']
        self.assertEqual(backward2.encode(backward2.pack(lines)),
                         'SEND\nheader1:test\xe6\x9d\xb1')
        lines = ['SEND', '\n', u'header1:test', '\xe6\x9d\xb1']
        self.assertEqual(backward2.encode(backward2.pack(lines)),
                         'SEND\nheader1:test\xe6\x9d\xb1')

    def test_decode(self):
        self.assertTrue(backward2.decode(None) is None)
        self.assertEqual(b'test', backward2.decode(b'test'))

    def test_encode(self):
        self.assertEqual(b'test', backward2.encode(u'test'))
        self.assertEqual(b'test', backward2.encode(b'test'))
