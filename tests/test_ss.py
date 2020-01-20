import time

import pytest

import stomp
from stomp.listener import *
from .testutils import *


@pytest.fixture
def server():
    server = StubStompServer("127.0.0.1", 60000)
    server.start()
    yield server
    server.stop()


class TestWithStompServer(object):

    def test_disconnect(self, server):
        server.add_frame('''CONNECTED
version:1.1
session:1
server:test
heart-beat:1000,1000

\x00''')

        conn = stomp.Connection([("127.0.0.1", 60000)])
        listener = TestListener(print_to_log=True)
        conn.set_listener('', listener)
        conn.connect()

        time.sleep(2)

        server.stop()

        for _ in range(100):
            if server.stopped:
                break
            time.sleep(0.1)
        else:
            assert False, "server never disconnected"

        time.sleep(1)

        try:
            conn.send(body="test disconnect", destination="/test/disconnectqueue")
            pytest.fail("Should not have successfully sent a message at this point")
        except Exception:
            _, e, _ = sys.exc_info()
            if e.__class__ == AssertionError:
                pytest.fail(str(e))
            logging.debug("stopping conn after expected exception %s", e)
            # lost connection, now restart the server
            try:
                conn.disconnect(receipt=None)
            except:
                pass

            time.sleep(2)

            server.add_frame('''CONNECTED
version:1.1
session:1
server:test
heart-beat:1000,1000

\x00''')

            server.start()

            conn.connect()

            time.sleep(5)

        assert listener.connections >= 2, "should have received 2 connection acknowledgements"

    def test_parsing(self, server):

        def pump(n):
            # pump; test server gives us one frame per received something
            for x in range(n):
                if x == 0:
                    logging.debug("pump sending %s frames" % n)
                conn.transport.send(b"\n")
                time.sleep(0.01)

        # Trailing optional EOLs in a frame

        server.add_frame('''CONNECTED
version:1.1
session:1
server:test
heart-beat:1000,1000

\x00''' + "\n\n\n")
        expected_heartbeat_count = 0

        conn = stomp.Connection([("127.0.0.1", 60000)], heartbeats=(1000,1000))
        listener = TestListener(print_to_log=True)
        conn.set_listener('', listener)
        conn.connect()

        logging.info("test parsing (1) expected hb count is %s", expected_heartbeat_count)
        assert expected_heartbeat_count == listener.heartbeat_count, "(1) expected hb count %s, was %s" % (expected_heartbeat_count, listener.heartbeat_count)

        # No trailing EOLs, separate heartbeat

        message_body = "Hello\n...world!"
        message_frame = '''MESSAGE
content-type:text/plain

%s\x00''' % message_body

        server.add_frame(message_frame)
        server.add_frame("\n")
        expected_heartbeat_count += 1

        pump(2)

        logging.info("test parsing (2) expected hb count is %s", expected_heartbeat_count)

        listener.wait_for_heartbeat()
        headers, body = listener.get_latest_message()

        assert expected_heartbeat_count == listener.heartbeat_count, "(2) expected hb count %s, was %s" % (expected_heartbeat_count, listener.heartbeat_count)
        assert {"content-type": "text/plain"} == headers
        assert message_body == body

        # Trailing EOL, separate heartbeat, another message

        server.add_frame(message_frame + "\n")
        server.add_frame("\n")
        server.add_frame(message_frame + "\n")
        expected_heartbeat_count += 1

        pump(3)

        logging.info("test parsing (3) expected hb count is %s", expected_heartbeat_count)

        listener.wait_for_heartbeat()
        listener.wait_for_message()
        headers, body = listener.get_latest_message()

        assert expected_heartbeat_count == listener.heartbeat_count, "(3) expected hb count %s, was %s" % (expected_heartbeat_count, listener.heartbeat_count)
        assert {"content-type": "text/plain"} == headers
        assert message_body == body

        # Torture tests: return content one byte at a time

        server.add_frame("\n")
        server.add_frame(message_frame)
        server.add_frame("\n")
        expected_heartbeat_count += 2

        pump(len(message_frame) + 2)

        logging.info("test parsing (4) expected hb count is %s", expected_heartbeat_count)

        listener.wait_for_heartbeat()
        headers, body = listener.get_latest_message()

        assert expected_heartbeat_count == listener.heartbeat_count, "(4) expected hb count %s, was %s" % (expected_heartbeat_count, listener.heartbeat_count)
        assert {"content-type": "text/plain"} == headers
        assert message_body == body

        # ...and a similar one with content-length and null bytes in body

        message_body = "%s\x00\x00%s" % (message_body, message_body)
        message_frame = '''MESSAGE
content-type:text/plain
content-length:%s

%s\x00''' % (len(message_body), message_body)

        server.add_frame("\n")
        server.add_frame("\n")
        server.add_frame(message_frame)
        server.add_frame("\n")
        expected_heartbeat_count += 3

        pump(len(message_frame) + 3)

        logging.info("test parsing (5) expected hb count is %s", expected_heartbeat_count)

        listener.wait_for_heartbeat()
        headers, body = listener.get_latest_message()

        assert expected_heartbeat_count == listener.heartbeat_count, "(5) expected hb count %s, was %s" % (expected_heartbeat_count, listener.heartbeat_count)
        assert {
            "content-type": "text/plain",
            "content-length": str(len(message_body)),
        } == headers
        assert message_body == body
