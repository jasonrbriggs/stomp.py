import unittest

from stomp import backward2

class TestBackward2(unittest.TestCase):
    def test_decode(self):
        self.assertTrue(backward2.decode(None) is None)
        self.assertEquals(b'test', backward2.decode(b'test'))

    def test_encode(self):
        self.assertEquals(b'test', backward2.encode(u'test'))
        self.assertEquals(b'test', backward2.encode(b'test'))