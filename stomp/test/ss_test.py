try:
    from exceptions import AssertionError
except ImportError:
    pass
import logging
import sys
import time
import unittest

import stomp
from stomp.listener import TestListener
from stomp.test.testutils import *

log = logging.getLogger('ss_test.py')


class TestWithStompServer(unittest.TestCase):

    def setUp(self):
        self.server = TestStompServer('127.0.0.1', 60000)
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def test_disconnect(self):
        self.server.add_frame('''CONNECTED
version:1.1
session:1
server:test
heart-beat:1000,1000

\x00''')

        conn = stomp.Connection([('127.0.0.1', 60000)])
        listener = TestListener()
        conn.set_listener('', listener)
        conn.start()
        conn.connect()

        time.sleep(2)

        self.server.stop()

        for _ in range(100):
            if self.server.stopped:
                break
            time.sleep(0.1)
        else:
            assert False, 'server never disconnected'

        time.sleep(1)

        try:
            conn.send(body='test disconnect', destination='/test/disconnectqueue')
            self.fail('Should not have successfully sent a message at this point')
        except Exception:
            _, e, _ = sys.exc_info()
            if e.__class__ == AssertionError:
                self.fail(str(e))
            log.debug('stopping conn after expected exception %s', e)
            # lost connection, now restart the server
            try:
                conn.disconnect(receipt=None)
            except:
                pass

            time.sleep(2)

            self.server.add_frame('''CONNECTED
version:1.1
session:1
server:test
heart-beat:1000,1000

\x00''')

            self.server.start()

            conn.start()
            conn.connect()

            time.sleep(5)

        self.assertTrue(listener.connections >= 2, 'should have received 2 connection acknowledgements')

    def test_parsing(self):

        def pump(n):
            # pump; test server gives us one frame per received something
            for _ in range(n):
                conn.transport.send(b'\n')
                time.sleep(0.01)

        # Trailing optional EOLs in a frame

        self.server.add_frame('''CONNECTED
version:1.1
session:1
server:test
heart-beat:1000,1000

\x00''' + '\n\n\n')
        expected_heartbeat_count = 0

        conn = stomp.Connection([('127.0.0.1', 60000)])
        listener = TestListener()
        conn.set_listener('', listener)
        conn.start()
        conn.connect()

        time.sleep(2)

        self.assertEqual(expected_heartbeat_count, listener.heartbeat_count)

        # No trailing EOLs, separate heartbeat

        message_body = 'Hello\n...world!'
        message_frame = '''MESSAGE
content-type:text/plain

%s\x00''' % message_body

        self.server.add_frame(message_frame)
        self.server.add_frame('\n')
        expected_heartbeat_count += 1

        pump(2)

        listener.wait_for_heartbeat()
        headers, body = listener.get_latest_message()

        self.assertEqual(expected_heartbeat_count, listener.heartbeat_count)
        self.assertEqual({"content-type": "text/plain"}, headers)
        self.assertEqual(message_body, body)

        # Trailing EOL, separate heartbeat, another message

        self.server.add_frame(message_frame + '\n')
        self.server.add_frame('\n')
        self.server.add_frame(message_frame + '\n')
        expected_heartbeat_count += 1

        pump(3)

        listener.wait_for_heartbeat()
        listener.wait_for_message()
        headers, body = listener.get_latest_message()

        self.assertEqual(expected_heartbeat_count, listener.heartbeat_count)
        self.assertEqual({"content-type": "text/plain"}, headers)
        self.assertEqual(message_body, body)

        # Torture tests: return content one byte at a time

        self.server.add_frame('\n')
        for c in message_frame:
            self.server.add_frame(c)
        self.server.add_frame('\n')
        expected_heartbeat_count += 2

        pump(len(message_frame) + 2)

        listener.wait_for_heartbeat()
        headers, body = listener.get_latest_message()

        self.assertEqual(expected_heartbeat_count, listener.heartbeat_count)
        self.assertEqual({"content-type": "text/plain"}, headers)
        self.assertEqual(message_body, body)

        # ...and a similar one with content-length and null bytes in body

        message_body = '%s\x00\x00%s' % (message_body, message_body)
        message_frame = '''MESSAGE
content-type:text/plain
content-length:%s

%s\x00''' % (len(message_body), message_body)

        self.server.add_frame('\n')
        self.server.add_frame('\n')
        for c in message_frame:
            self.server.add_frame(c)
        self.server.add_frame('\n')
        expected_heartbeat_count += 3

        pump(len(message_frame) + 3)

        listener.wait_for_heartbeat()
        headers, body = listener.get_latest_message()

        self.assertEqual(expected_heartbeat_count, listener.heartbeat_count)
        self.assertEqual({
            "content-type": "text/plain",
            "content-length": str(len(message_body)),
        }, headers)
        self.assertEqual(message_body, body)
