import unittest

from stomp.utils import *

class TestUtils(unittest.TestCase):
    def testReturnsTrueWhenLocalhost(self):
        self.assertEquals(1, is_localhost(('localhost', 8000)))
        self.assertEquals(1, is_localhost(('127.0.0.1', 8000)))
        self.assertEquals(2, is_localhost(('192.168.1.92', 8000)))