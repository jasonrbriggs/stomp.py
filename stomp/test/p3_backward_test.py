import unittest

from stomp import backward3


class TestBackward3(unittest.TestCase):
    def test_decode(self):
        self.assertTrue(backward3.decode(None) is None)
        self.assertEqual('test', backward3.decode(b'test'))

    def test_encode(self):
        self.assertEqual(b'test', backward3.encode('test'))
        self.assertEqual(b'test', backward3.encode(b'test'))
        self.assertRaises(TypeError, backward3.encode, None)

    def test_pack(self):
        self.assertEquals(b'testtest', backward3.pack([b'test', b'test']))