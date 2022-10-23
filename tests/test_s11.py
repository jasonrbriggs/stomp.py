import stomp
from stomp.listener import *
from .testutils import *
import time

class Test11Send(object):
    """
    def test11(self):
        conn = stomp.Connection(get_default_host())
        tl = TestListener("123", print_to_log=False)
        conn.set_listener('testlistener', tl)
        wl = WaitingListener("DISCONNECT1")
        conn.set_listener("waiting", wl)
        conn.connect(get_default_user(), get_default_password(), wait=True)
        conn.subscribe(destination="/queue/test", ack="auto", id=1)

        conn.send(body="this is a test", destination="/queue/test", receipt="123")

        logging.info("WAIT FOR MESSAGE start")
        tl.wait_for_message()
        logging.info("WAIT FOR MESSAGE end")

        assert tl.connections == 1, "should have received 1 connection acknowledgement"
        assert tl.messages >= 1, "should have received at least 1 message"
        assert tl.errors == 0, "should not have received any errors"

        conn.unsubscribe(destination="/queue/test", id=1)

        # stomp1.1 disconnect with receipt
        conn.disconnect(receipt="DISCONNECT1")

        # wait for the receipt
        wl.wait_on_receipt()
        wl.wait_on_disconnected()

        logging.info("Stats: %s" % str(tl))

    def testheartbeat(self):
        conn = stomp.Connection(get_default_host(), heartbeats=(2000, 3000))
        listener = TestListener("123", print_to_log=True)
        conn.set_listener('', listener)
        conn.connect(get_default_user(), get_default_password(), wait=True)
        assert conn.heartbeats[0] > 0
        conn.subscribe(destination="/queue/test", ack="auto", id=1)

        conn.send(body="this is a test", destination="/queue/test", receipt="123")

        listener.wait_for_message()
        conn.disconnect(receipt=None)

        assert listener.connections >= 1, "should have received 1 connection acknowledgement, was %s" % listener.connections
        assert listener.messages >= 1, "should have received 1 message, was %s" % listener.messages
        assert listener.errors == 0, "should not have received any errors, was %s" % listener.errors
        assert listener.heartbeat_timeouts == 0, "should not have received a heartbeat timeout, was %s" % listener.heartbeat_timeouts
    """
    def testheartbeat_timeout(self):
        server = StubStompServer("127.0.0.1", 60000)
        server.start()
        try:
            server.add_frame('''CONNECTED
version:1.1
session:1
server:test
heart-beat:1000,1000

\x00''')

            conn = stomp.Connection([("127.0.0.1", 60000)], heartbeats=(10000, 1000))
            listener = TestListener(print_to_log=True)
            conn.set_listener('', listener)
            conn.connect()

            time.sleep(5)

            logging.info("@>>>>>>>>>>>>>>>>>TIMEOUTS %s", listener.heartbeat_timeouts)

            server.running = False
        except Exception:
            _, e, _ = sys.exc_info()
            logging.error("error: %s", e)
        finally:
            server.stop()

        logging.debug(">>>>> %s", listener.heartbeat_timeouts)
        assert listener.heartbeat_timeouts >= 1, "should have received a heartbeat timeout"
    """
    def testheartbeat_shutdown(self):
        server = StubStompServer("127.0.0.1", 60000)
        server.start()
        conn = None
        try:
            server.add_frame('''CONNECTED
version:1.1
session:1
server:test
heart-beat:1000,1000

\x00''')

            conn = stomp.Connection([("127.0.0.1", 60000)], heartbeats=(10000, 10000))
            listener = TestListener(print_to_log=True)
            conn.set_listener('', listener)
            conn.connect()

            start_time = time.time()
            time.sleep(0.5)
            # shutdown connection
            server.stop()
            while conn.heartbeat_thread is not None:
                time.sleep(0.5)
            end_time = time.time()

            server.running = False
        except Exception:
            _, e, _ = sys.exc_info()
            logging.error("error: %s", e)

        assert end_time - start_time <= 2, "should stop immediately and not after heartbeat timeout"
        assert conn.heartbeat_thread is None, "heartbeat thread should have finished"
"""