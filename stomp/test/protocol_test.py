import copy
import time
import unittest

from mock import Mock

import stomp
from stomp.protocol import *
from stomp.test.testutils import *


class Test11Protocol(unittest.TestCase):
    def setUp(self):
        transport = Mock()
        self.protocol = Protocol11(transport)
    
    def test_escape_headers_check(self):
        hdrs = {'test': '\n\r:\\'}
        
        self.protocol._escape_headers(hdrs)
        self.protocol._escape_headers(hdrs)
        
        self.assertEqual('\\n\r\\c\\\\', hdrs['test'])
    
    def test_escape_headers(self):
        hdrs = {'expires': '0', 'timestamp': '1452527028845', 'destination': '/topic/FOO', 'persistent': 'true', 'priority': '4', 'message-id': 'ID:520969-foobar-52253-1451938805275-0:0:2:392022:1', 'subscription': '3'}
        
        self.protocol._escape_headers(hdrs)
        
        chk_hdrs = copy.deepcopy(hdrs)
        
        self.protocol._escape_headers(hdrs)
        self.protocol._escape_headers(hdrs)
        self.protocol._escape_headers(hdrs)
        
        shared_items = set(hdrs.items()) & set(chk_hdrs.items())
        self.assertEqual(len(chk_hdrs), len(shared_items))


class Test12Protocol(unittest.TestCase):
    def setUp(self):
        transport = Mock()
        self.protocol = Protocol12(transport)
    
    def test_escape_headers_check(self):
        hdrs = {'test': '\n\r:\\'}
        
        self.protocol._escape_headers(hdrs)
        self.protocol._escape_headers(hdrs)
        
        self.assertEqual('\\n\\r\\c\\\\', hdrs['test'])
    
    def test_escape_headers(self):
        hdrs = {'expires': '0', 'timestamp': '1452527028845', 'destination': '/topic/FOO', 'persistent': 'true', 'priority': '4', 'message-id': 'ID:520969-foobar-52253-1451938805275-0:0:2:392022:1', 'subscription': '3'}
        
        self.protocol._escape_headers(hdrs)
        
        chk_hdrs = copy.deepcopy(hdrs)
        
        self.protocol._escape_headers(hdrs)
        self.protocol._escape_headers(hdrs)
        self.protocol._escape_headers(hdrs)
        
        shared_items = set(hdrs.items()) & set(chk_hdrs.items())
        self.assertEqual(len(chk_hdrs), len(shared_items))
