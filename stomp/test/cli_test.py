import tempfile
import time
import unittest

from stomp.__main__ import StompCLI
from stomp.test.testutils import *

username = get_default_user()
password = get_default_password()

(host, port) = get_default_host()[0]

test_text = '''subscribe /queue/testfile
send /queue/testfile this is a test
unsubscribe /queue/testfile'''


def create_test_file():
    with tempfile.NamedTemporaryFile('w', delete=False) as f:
        f.write('''subscribe /queue/testfile
send /queue/testfile this is a test
unsubscribe /queue/testfile''')
    return f


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
        f = create_test_file()

        teststdin = TestStdin()
        teststdout = TestStdout(self)
        teststdout.expect('CONNECTED')

        cli = StompCLI(host, port, username, password, '1.0', stdin=teststdin, stdout=teststdout)

        time.sleep(3)

        cli.onecmd('sendfile /queue/testsendfile %s' % f.name)

        time.sleep(3)

        teststdout.expect('Shutting down, please wait')
        cli.onecmd('quit')

    def testsendfileheaders(self):
        f = create_test_file()

        teststdin = TestStdin()
        teststdout = TestStdout(self)
        teststdout.expect('CONNECTED')

        cli = StompCLI(host, port, username, password, '1.0', stdin=teststdin, stdout=teststdout)

        time.sleep(3)

        cli.onecmd('sendfile /queue/testsendfile %s { "custom" : "header" }' % f.name)

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
        f = create_test_file()

        teststdin = TestStdin()
        teststdout = TestStdout(self)
        teststdout.expect('CONNECTED')

        cli = StompCLI(host, port, username, password, '1.0', stdin=teststdin, stdout=teststdout)

        time.sleep(3)

        teststdout.expect('Subscribing to "/queue/testfile" with acknowledge set to "auto", id set to "1"')
        teststdout.expect('this is a test')
        teststdout.expect('MESSAGE')
        teststdout.expect('Unsubscribing from "/queue/testfile"')
        cli.onecmd('run %s' % f.name)
        teststdout.expect('Shutting down, please wait')
        cli.onecmd('quit')

    def testrunarg(self):
        f = create_test_file()

        teststdin = TestStdin()
        teststdout = TestStdout(self)
        teststdout.expect('CONNECTED')

        cli = StompCLI(host, port, username, password, '1.0', stdin=teststdin, stdout=teststdout)

        time.sleep(3)

        teststdout.expect('Subscribing to "/queue/testfile" with acknowledge set to "auto", id set to "1"')
        teststdout.expect('this is a test')
        teststdout.expect('MESSAGE')
        teststdout.expect('Unsubscribing from "/queue/testfile"')

        cli.do_run(f.name)

        teststdout.expect('Shutting down, please wait')
        cli.onecmd('quit')
