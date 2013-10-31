import os
import re
import time
import unittest

from stomp.__main__ import StompCLI

header_re = re.compile(r'[^:]+:.*')

from testutils import *

username = 'admin'
password = 'password'

host = os.environ['STD_HOST']
port = int(os.environ['STD_PORT'])

class TestStdin:
    pass
    
class TestStdout:
    def __init__(self, test):
        self.test = test
        self.expects = []
    
    def expect(self, txt):
        self.expects.insert(0, re.compile(txt))
        
    def write(self, txt):
        txt = txt.rstrip()
        if txt != '':
            print(txt)
        if txt == '>' or txt == '' or header_re.match(txt):
            return
        if len(self.expects) == 0:
            self.test.fail('No expectations - actual "%s"' % txt)
            return

        for x in range(0, len(self.expects)):
            chk = self.expects[x]
            if chk.match(txt):
                del self.expects[x]
                return
        
        self.test.fail('"%s" was not expected' % txt)
            
    def flush(self):
        pass

class TestCLI(unittest.TestCase):

    def setUp(self):
        pass

    def testsubscribe(self):
        stdin = TestStdin()
        stdout = TestStdout(self)
        stdout.expect('CONNECTED')
        
        cli = StompCLI(host, port, username, password, 1.0, stdin, stdout)
        
        time.sleep(3)
        
        stdout.expect('Subscribing to "/queue/testsubscribe" with acknowledge set to "auto", id set to "1"')
        cli.onecmd('subscribe /queue/testsubscribe')
        stdout.expect('MESSAGE')
        stdout.expect('this is a test')
        cli.onecmd('send /queue/testsubscribe this is a test')
        
        time.sleep(3)
        
        stdout.expect('Unsubscribing from "/queue/testsubscribe"')
        cli.onecmd('unsubscribe /queue/testsubscribe')      
        cli.onecmd('quit')

    def testsendrec(self):
        stdin = TestStdin()
        stdout = TestStdout(self)
        
        stdout.expect('CONNECTED')
        
        cli = StompCLI(host, port, username, password, 1.0, stdin, stdout)

        time.sleep(3)

        stdout.expect('RECEIPT')
        cli.onecmd('sendrec /queue/testsendrec this is a test')

        time.sleep(3)

        cli.onecmd('quit')
            
    def testsendfile(self):
        stdin = TestStdin()
        stdout = TestStdout(self)
        stdout.expect('CONNECTED')
        
        cli = StompCLI(host, port, username, password, 1.0, stdin, stdout)

        time.sleep(3)

        cli.onecmd('sendfile /queue/testsendfile stomp/test/test.txt')

        time.sleep(3)

        cli.onecmd('quit')

    def testabort(self):
        stdin = TestStdin()
        stdout = TestStdout(self)
        stdout.expect('CONNECTED')
        
        cli = StompCLI(host, port, username, password, 1.0, stdin, stdout)

        time.sleep(3)

        stdout.expect('Subscribing to "/queue/testabort" with acknowledge set to "auto", id set to "1"')
        cli.onecmd('subscribe /queue/testabort')
        
        cli.onecmd('begin')        
        cli.onecmd('send /queue/testabort this is a test')
        cli.onecmd('abort')

        time.sleep(3)

        stdout.expect('Unsubscribing from "/queue/testabort"')
        cli.onecmd('unsubscribe /queue/testabort')
        cli.onecmd('quit')
            
    def testcommit(self):
        stdin = TestStdin()
        stdout = TestStdout(self)
        stdout.expect('CONNECTED')
        
        cli = StompCLI(host, port, username, password, 1.0, stdin, stdout)

        time.sleep(3)

        stdout.expect('Subscribing to "/queue/testcommit" with acknowledge set to "auto", id set to "1"')
        cli.onecmd('subscribe /queue/testcommit')

        cli.onecmd('begin')        
        cli.onecmd('send /queue/testcommit this is a test')
        
        stdout.expect('Committing.*')
        stdout.expect('MESSAGE')
        stdout.expect('this is a test')
        cli.onecmd('commit')

        time.sleep(3)

        stdout.expect('Unsubscribing from "/queue/testcommit"')
        cli.onecmd('unsubscribe /queue/testcommit')
        cli.onecmd('quit')

    def teststats(self):
        stdin = TestStdin()
        stdout = TestStdout(self)
        stdout.expect('CONNECTED')
        
        cli = StompCLI(host, port, username, password, 1.0, stdin, stdout)

        time.sleep(3)

        stdout.expect('Subscribing to "/queue/teststats" with acknowledge set to "auto", id set to "1"')
        cli.onecmd('subscribe /queue/teststats')
        
        stdout.expect('.*No stats available.*')
        cli.onecmd('stats')
        
        time.sleep(1)
        
        cli.onecmd('stats on')
        cli.onecmd('send /queue/teststats this is a test')

        stdout.expect('MESSAGE')
        stdout.expect('this is a test')

        time.sleep(3)
        
        cli.onecmd('stats')

        stdout.expect('Unsubscribing from "/queue/teststats"')
        cli.onecmd('unsubscribe /queue/teststats')
        cli.onecmd('quit')
            
    def testrun(self):
        stdin = TestStdin()
        stdout = TestStdout(self)
        stdout.expect('CONNECTED')
        
        cli = StompCLI(host, port, username, password, 1.0, stdin, stdout)

        time.sleep(3)
        
        stdout.expect('Subscribing to "/queue/testfile" with acknowledge set to "auto", id set to "1"')
        stdout.expect('this is a test')
        stdout.expect('MESSAGE')
        stdout.expect('Unsubscribing from "/queue/testfile"')
        cli.onecmd('run stomp/test/test.txt')      
        cli.onecmd('quit')

    def testrunarg(self):
        stdin = TestStdin()
        stdout = TestStdout(self)
        stdout.expect('CONNECTED')

        cli = StompCLI(host, port, username, password, 1.0, stdin, stdout)

        time.sleep(3)

        stdout.expect('Subscribing to "/queue/testfile" with acknowledge set to "auto", id set to "1"')
        stdout.expect('this is a test')
        stdout.expect('MESSAGE')
        stdout.expect('Unsubscribing from "/queue/testfile"')

        cli.do_run('stomp/test/test.txt')
