import time
import unittest

import stomp
from stomp import exception

from testutils import TestListener, TestStompServer

import logging
log = logging.getLogger('ss_test.py')

class TestWithStompServer(unittest.TestCase):
   
    def testdisconnect(self):
        server = TestStompServer('127.0.0.1', 60000)
        try:
            server.start()
        
            server.add_frame('''CONNECTED
version: 1.1
session: 1
server: test
heart-beat: 1000,1000\x00''')
        
            conn = stomp.Connection([('127.0.0.1', 60000)], version = 1.0)
            listener = TestListener()
            conn.set_listener('', listener)
            conn.start()
            conn.connect()

            time.sleep(2)

            server.stop()

            while not server.stopped:
                time.sleep(0.1)

            try:
                conn.send('test disconnect', destination='/test/disconnectqueue')
                self.fail('Should not have successfully sent a message at this point')
            except Exception:
                log.debug('stopping conn')
                # lost connection, now restart the server
                try:
                    conn.stop()
                except:
                    pass

                time.sleep(2)

                server.add_frame('''CONNECTED
    version: 1.1
    session: 1
    server: test
    heart-beat: 1000,1000\x00''')

                server.start()

                conn.start()
                conn.connect()

                time.sleep(5)

            self.assert_(listener.connections >= 2, 'should have received 2 connection acknowledgements')

            time.sleep(2)
        finally:
            server.stop()
    
