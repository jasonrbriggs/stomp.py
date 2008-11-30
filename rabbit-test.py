import time
import sys

import stomp

class MyListener(object):
    def on_error(self, headers, message):
        print 'received an error %s' % message

    def on_connecting(self, host_and_port):
        print host_and_port
        
    def on_message(self, headers, message):
        print 'received a message %s' % message

conn = stomp.Connection([('0.0.0.0', 61613), ('127.0.0.1', 61613)], 'guest', 'guest')
conn.add_listener(MyListener())
conn.start()
conn.connect()

conn.subscribe(destination='/queue/test', ack='auto')

conn.send(' '.join(sys.argv[1:]), destination='/queue/test')

time.sleep(2)
conn.disconnect()
