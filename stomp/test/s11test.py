import time
import unittest

import stomp
from stomp import exception
from stomp import listener

import testlistener

class Test11Send(unittest.TestCase):

    def setUp(self):
        pass

    def test11(self):
        conn = stomp.Connection([('127.0.0.2', 61613), ('localhost', 61613)], 'admin', 'password', version=1.1)
        tl = testlistener.TestListener()
        conn.set_listener('', tl)
        conn.start()
        conn.connect(wait=True)
        conn.subscribe(destination='/queue/test', ack='auto', id=1)

        conn.send('this is a test', destination='/queue/test')

        time.sleep(3)

        self.assert_(tl.connections == 1, 'should have received 1 connection acknowledgement')
        self.assert_(tl.messages >= 1, 'should have received at least 1 message')
        self.assert_(tl.errors == 0, 'should not have received any errors')
        
        conn.unsubscribe(destination='/queue/test', id=1)
        
        wl = listener.WaitingListener('DISCONNECT1')
        conn.set_listener('waiting', wl)
        
        # stomp1.1 disconnect with receipt
        conn.disconnect(headers={'receipt' : 'DISCONNECT1'})
        
        # wait for the receipt
        wl.wait_on_receipt()
        
        # unnecessary... but anyway
        self.assert_(wl.received == True)
        
suite = unittest.TestLoader().loadTestsFromTestCase(Test11Send)
unittest.TextTestRunner(verbosity=2).run(suite)
