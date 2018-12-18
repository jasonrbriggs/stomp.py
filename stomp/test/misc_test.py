import time
import traceback
import unittest
import xml.dom.minidom

import stomp
from stomp.exception import *
from stomp.listener import *
from stomp.test.testutils import *


log = logging.getLogger('stomp.py')


class TransformationListener(TestListener):
    def __init__(self, receipt):
        TestListener.__init__(self, receipt)
        self.message = None

    def on_before_message(self, headers, body):
        if 'transformation' in headers:
            trans_type = headers['transformation']
            if trans_type != 'jms-map-xml':
                return body

            try:
                entries = {}
                doc = xml.dom.minidom.parseString(body)
                rootElem = doc.documentElement
                for entryElem in rootElem.getElementsByTagName("entry"):
                    pair = []
                    for node in entryElem.childNodes:
                        if not isinstance(node, xml.dom.minidom.Element):
                            continue
                        pair.append(node.firstChild.nodeValue)
                    assert len(pair) == 2
                    entries[pair[0]] = pair[1]
                return (headers, entries)
            except Exception:
                #
                # unable to parse message. return original
                #
                traceback.print_exc()
                return (headers, body)

    def on_message(self, headers, body):
        TestListener.on_message(self, headers, body)
        self.message = body


class TestMessageTransform(unittest.TestCase):

    def setUp(self):
        conn = stomp.Connection(get_rabbitmq_host())
        listener = TransformationListener('123')
        conn.set_listener('', listener)
        conn.connect(get_rabbitmq_user(), get_rabbitmq_password(), wait=True)
        self.conn = conn
        self.listener = listener
        self.timestamp = time.strftime('%Y%m%d%H%M%S')

    def tearDown(self):
        if self.conn:
            self.conn.disconnect(receipt=None)

    def test_transform(self):
        queuename = '/queue/testtransform-%s' % self.timestamp
        self.conn.subscribe(destination=queuename, id=1, ack='auto')

        self.conn.send(body='''<map>
    <entry>
        <string>name</string>
        <string>Dejan</string>
    </entry>
    <entry>
        <string>city</string>
        <string>Belgrade</string>
    </entry>
</map>''', destination=queuename, headers={'transformation': 'jms-map-xml'}, receipt='123')

        self.listener.wait_on_receipt()
        self.listener.wait_for_message()

        self.assertTrue(self.listener.message is not None, 'Did not receive a message')
        self.assertTrue(self.listener.message.__class__ == dict,
            'Message type should be dict after transformation, was %s' % self.listener.message.__class__)
        self.assertTrue(self.listener.message['name'] == 'Dejan', 'Missing an expected dict element')
        self.assertTrue(self.listener.message['city'] == 'Belgrade', 'Missing an expected dict element')


class TestNoResponseConnectionKill(unittest.TestCase):
    def setUp(self):
        self.server = TestStompServer('127.0.0.1', 60000)
        self.server.start()
        self.timeout_thread = threading.Thread(name='shutdown test server', target=self.timeout_server)

    def timeout_server(self):
        time.sleep(3)
        log.info('Stopping server')
        self.server.running = False
        self.server.stop()

    def test_noresponse(self):
        try:
            conn = stomp.Connection([('127.0.0.1', 60000)], heartbeats=(1000, 1000))
            listener = TestListener()
            conn.set_listener('', listener)
            self.timeout_thread.start()
            conn.connect(wait=True)
            self.fail("Shouldn't happen")
        except ConnectFailedException:
            log.info('Received connect failed - test success')
        except Exception:
            self.fail("Shouldn't happen")

