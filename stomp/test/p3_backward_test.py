import unittest

from stomp import backward3

class TestBackward3(unittest.TestCase):
    def test_decode(self):
        self.assertTrue(backward3.decode(None) is None)
        self.assertEquals('test', backward3.decode(b'test'))

    def test_encode(self):
        self.assertEquals(b'test', backward3.encode(u'test'))
        self.assertEquals(b'test', backward3.encode(b'test'))
        self.assertRaises(TypeError, backward3.encode, None)