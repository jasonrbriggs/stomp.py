import importlib
import inspect
import logging
import platform
import traceback
import xml.dom.minidom

import pytest

import stomp
from stomp.exception import *
from stomp.listener import *
from .testutils import *


class TransformationListener(TestListener):
    def __init__(self, receipt, print_to_log):
        TestListener.__init__(self, receipt, print_to_log)
        self.message = None

    def on_before_message(self, frame):
        if "transformation" in frame.headers:
            trans_type = frame.headers["transformation"]
            if trans_type != "jms-map-xml":
                return

            try:
                entries = {}
                doc = xml.dom.minidom.parseString(frame.body)
                rootElem = doc.documentElement
                for entryElem in rootElem.getElementsByTagName("entry"):
                    pair = []
                    for node in entryElem.childNodes:
                        if not isinstance(node, xml.dom.minidom.Element):
                            continue
                        pair.append(node.firstChild.nodeValue)
                    assert len(pair) == 2
                    entries[pair[0]] = pair[1]
                frame.body = entries
            except Exception:
                #
                # unable to parse message. return original
                #
                traceback.print_exc()

    def on_message(self, frame):
        TestListener.on_message(self, frame)
        self.message = frame


class HeaderModListener(TestListener):
    def on_before_message(self, frame):
        frame.headers["testheader"] = "modifiedheader"

    def on_message(self, frame):
        TestListener.on_message(self, frame)
        self.message = frame


@pytest.fixture()
def conn():
    conn = stomp.Connection11(get_rabbitmq_host())
    conn.set_listener("testlistener", TransformationListener("123", print_to_log=True))
    conn.connect(get_rabbitmq_user(), get_rabbitmq_password(), wait=True)
    yield conn
    conn.disconnect(receipt=None)


@pytest.fixture()
def conn2():
    conn2 = stomp.Connection11(get_rabbitmq_host())
    conn2.set_listener("testlistener", HeaderModListener("123", print_to_log=True))
    conn2.connect(get_rabbitmq_user(), get_rabbitmq_password(), wait=True)
    yield conn2
    conn2.disconnect(receipt=None)


def timeout_server(svr):
    time.sleep(3)
    logging.info("Stopping server %s" % svr)
    svr.running = False
    svr.stop()


@pytest.fixture()
def miscserver():
    server = StubStompServer("127.0.0.1", 60000)
    server.start()
    yield server


@pytest.fixture()
def timeout_thread(miscserver):
    timeout_thread = threading.Thread(name="shutdown test server", target=timeout_server, args=(miscserver,))
    yield timeout_thread


class TestMessageTransform(object):
    def test_transform(self, conn):
        listener = conn.get_listener("testlistener")
        queuename = "/queue/testtransform-%s" % listener.timestamp
        conn.subscribe(destination=queuename, id=1, ack="auto")

        conn.send(body='''<map>
    <entry>
        <string>name</string>
        <string>Dejan</string>
    </entry>
    <entry>
        <string>city</string>
        <string>Belgrade</string>
    </entry>
</map>''', destination=queuename, headers={"transformation": "jms-map-xml"}, receipt="123")

        listener.wait_on_receipt()
        listener.wait_for_message()

        message = listener.message.body
        assert message is not None, "Did not receive a message"
        assert type(message) == dict, "Message type should be dict after transformation, was %s" % message.__class__
        assert message["name"] == "Dejan", "Missing an expected dict element"
        assert message["city"] == "Belgrade", "Missing an expected dict element"


class TestNoResponseConnectionKill(object):

    def test_noresponse(self, miscserver, timeout_thread):
        try:
            conn = stomp.Connection([("127.0.0.1", 60000)], heartbeats=(1000, 1000))
            listener = TestListener(print_to_log=True)
            conn.set_listener("testlistener", listener)
            timeout_thread.start()
            conn.connect(wait=True)
            pytest.fail("Shouldn't happen")
        except ConnectFailedException:
            logging.info("Received connect failed - test success")
        except Exception as e:
            logging.error(e)
            pytest.fail("Shouldn't happen, error %s" % e)


class TestMiscellaneousLogic(object):
    def test_windows_colours(self, mocker):
        platform.system = mocker.MagicMock(return_value="Windows")
        import stomp.colours
        importlib.reload(stomp.colours)

        assert "" == stomp.colours.GREEN
        assert "" == stomp.colours.RED
        assert "" == stomp.colours.BOLD
        assert "" == stomp.colours.NO_COLOUR

    # just here for coverage
    def test_publisher(self):
        p = Publisher()
        p.set_listener("testlistener", None)
        p.remove_listener("testlistener")
        assert p.get_listener("testlistener") is None

    # coverage improvement since on_heartbeat is handled in subclasses of ConnectionListener
    def test_on_heartbeat(self):
        cl = ConnectionListener()
        cl.on_heartbeat()

    def test_heartbeatlistener(self, mocker):
        transport = mocker.MagicMock()
        hl = HeartbeatListener(transport, (10000,20000))
        hl.on_connected(Frame('heartbeat', {"heart-beat": "10000,20000"}, ''))
        time.sleep(1)
        hl.on_message

        # just check if there was a received heartbeat calculated
        assert hl.received_heartbeat > 0

    def test_original_headers(self, conn2):
        listener = conn2.get_listener("testlistener")
        queuename = "/queue/testheadermod-%s" % listener.timestamp
        conn2.subscribe(destination=queuename, id=1, ack="auto")

        conn2.send(body="test message", destination=queuename, headers={"testheader": "originalheader"}, receipt="123")

        listener.wait_on_receipt()
        listener.wait_for_message()

        assert "modifiedheader" == listener.message.headers["testheader"]
        assert "originalheader" == listener.message.original_headers["testheader"]
