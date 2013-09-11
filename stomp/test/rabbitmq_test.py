import time
import unittest

import stomp

from testutils import *

class TestRabbitMQSend(unittest.TestCase):

    def setUp(self):
        pass

    def testbasic(self):
        conn = stomp.Connection(get_rabbitmq_host(), 'guest', 'guest')
        listener = TestListener()
        conn.set_listener('', listener)
        conn.start()
        conn.connect(wait=True)
        conn.subscribe(destination='/queue/test', ack='auto')

        conn.send('this is a test', destination='/queue/test')

        time.sleep(2)
        conn.stop()

        self.assert_(listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assert_(listener.messages == 1, 'should have received 1 message')
        self.assert_(listener.errors == 0, 'should not have received any errors')


