import os
import re
import time
import unittest

from stomp.__main__ import StompCLI

header_re = re.compile(r'[^:]+:.*')

from stomp.test.testutils import *

username = 'admin'
password = 'password'

(host, port) = get_standard_host()[0]
(sslhost, sslport) = get_standard_ssl_host()[0]

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
        teststdin = TestStdin()
        teststdout = TestStdout(self)
        teststdout.expect('CONNECTED')

        cli = StompCLI(host, port, username, password, '1.0', stdin=teststdin, stdout=teststdout)

        time.sleep(3)

        teststdout.expect('Subscribing to "/queue/testsubscribe" with acknowledge set to "auto", id set to "1"')
        cli.onecmd('subscribe /queue/testsubscribe')
        teststdout.expect('MESSAGE')
        teststdout.expect('this is a test')
        cli.onecmd('send /queue/testsubscribe this is a test')

        time.sleep(3)

        teststdout.expect('Unsubscribing from "/queue/testsubscribe"')
        cli.onecmd('unsubscribe /queue/testsubscribe')
        teststdout.expect('Shutting down, please wait')
        cli.onecmd('quit')

    def testsendrec(self):
        teststdin = TestStdin()
        teststdout = TestStdout(self)

        teststdout.expect('CONNECTED')

        cli = StompCLI(host, port, username, password, '1.0', stdin=teststdin, stdout=teststdout)

        time.sleep(3)

        teststdout.expect('RECEIPT')
        cli.onecmd('sendrec /queue/testsendrec this is a test')

        time.sleep(3)

        teststdout.expect('Shutting down, please wait')
        cli.onecmd('quit')

    def testsendfile(self):
        teststdin = TestStdin()
        teststdout = TestStdout(self)
        teststdout.expect('CONNECTED')

        cli = StompCLI(host, port, username, password, '1.0', stdin=teststdin, stdout=teststdout)

        time.sleep(3)

        cli.onecmd('sendfile /queue/testsendfile stomp/test/test.txt')

        time.sleep(3)

        teststdout.expect('Shutting down, please wait')
        cli.onecmd('quit')

    def testabort(self):
        teststdin = TestStdin()
        teststdout = TestStdout(self)
        teststdout.expect('CONNECTED')

        cli = StompCLI(host, port, username, password, '1.0', stdin=teststdin, stdout=teststdout)

        time.sleep(3)

        teststdout.expect('Subscribing to "/queue/testabort" with acknowledge set to "auto", id set to "1"')
        cli.onecmd('subscribe /queue/testabort')

        cli.onecmd('begin')
        cli.onecmd('send /queue/testabort this is a test')
        cli.onecmd('abort')

        time.sleep(3)

        teststdout.expect('Unsubscribing from "/queue/testabort"')
        cli.onecmd('unsubscribe /queue/testabort')
        teststdout.expect('Shutting down, please wait')
        cli.onecmd('quit')

    def testcommit(self):
        teststdin = TestStdin()
        teststdout = TestStdout(self)
        teststdout.expect('CONNECTED')

        cli = StompCLI(host, port, username, password, '1.0', stdin=teststdin, stdout=teststdout)

        time.sleep(3)

        teststdout.expect('Subscribing to "/queue/testcommit" with acknowledge set to "auto", id set to "1"')
        cli.onecmd('subscribe /queue/testcommit')

        cli.onecmd('begin')
        cli.onecmd('send /queue/testcommit this is a test')

        teststdout.expect('Committing.*')
        teststdout.expect('MESSAGE')
        teststdout.expect('this is a test')
        cli.onecmd('commit')

        time.sleep(3)

        teststdout.expect('Unsubscribing from "/queue/testcommit"')
        cli.onecmd('unsubscribe /queue/testcommit')
        teststdout.expect('Shutting down, please wait')
        cli.onecmd('quit')

    def teststats(self):
        teststdin = TestStdin()
        teststdout = TestStdout(self)
        teststdout.expect('CONNECTED')

        cli = StompCLI(host, port, username, password, '1.0', stdin=teststdin, stdout=teststdout)

        time.sleep(3)

        teststdout.expect('Subscribing to "/queue/teststats" with acknowledge set to "auto", id set to "1"')
        cli.onecmd('subscribe /queue/teststats')

        teststdout.expect('.*No stats available.*')
        cli.onecmd('stats')

        time.sleep(1)

        cli.onecmd('stats on')
        cli.onecmd('send /queue/teststats this is a test')

        teststdout.expect('MESSAGE')
        teststdout.expect('this is a test')

        time.sleep(3)

        cli.onecmd('stats')

        teststdout.expect('Unsubscribing from "/queue/teststats"')
        cli.onecmd('unsubscribe /queue/teststats')
        teststdout.expect('Shutting down, please wait')
        cli.onecmd('quit')

    def testrun(self):
        teststdin = TestStdin()
        teststdout = TestStdout(self)
        teststdout.expect('CONNECTED')

        cli = StompCLI(host, port, username, password, '1.0', stdin=teststdin, stdout=teststdout)

        time.sleep(3)

        teststdout.expect('Subscribing to "/queue/testfile" with acknowledge set to "auto", id set to "1"')
        teststdout.expect('this is a test')
        teststdout.expect('MESSAGE')
        teststdout.expect('Unsubscribing from "/queue/testfile"')
        cli.onecmd('run stomp/test/test.txt')
        teststdout.expect('Shutting down, please wait')
        cli.onecmd('quit')

    def testrunarg(self):
        teststdin = TestStdin()
        teststdout = TestStdout(self)
        teststdout.expect('CONNECTED')

        cli = StompCLI(host, port, username, password, '1.0', stdin=teststdin, stdout=teststdout)

        time.sleep(3)

        teststdout.expect('Subscribing to "/queue/testfile" with acknowledge set to "auto", id set to "1"')
        teststdout.expect('this is a test')
        teststdout.expect('MESSAGE')
        teststdout.expect('Unsubscribing from "/queue/testfile"')

        cli.do_run('stomp/test/test.txt')

    def testssl(self):
        teststdin = TestStdin()
        teststdout = TestStdout(self)
        teststdout.expect('CONNECTED')

        cli = StompCLI(sslhost, sslport, username, password, '1.0', use_ssl=True, stdin=teststdin, stdout=teststdout)

        time.sleep(3)

        teststdout.expect('Subscribing to "/queue/testsubscribe" with acknowledge set to "auto", id set to "1"')
        cli.onecmd('subscribe /queue/testsubscribe')
        teststdout.expect('MESSAGE')
        teststdout.expect('this is a test')
        cli.onecmd('send /queue/testsubscribe this is a test')

        time.sleep(3)

        teststdout.expect('Unsubscribing from "/queue/testsubscribe"')
        cli.onecmd('unsubscribe /queue/testsubscribe')
        teststdout.expect('Shutting down, please wait')
        cli.onecmd('quit')
