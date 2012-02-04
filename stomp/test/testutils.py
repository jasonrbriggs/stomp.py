from stomp import ConnectionListener
import socket
import threading

import logging
log = logging.getLogger('testutils.py')

class TestListener(ConnectionListener):
    def __init__(self):
        self.errors = 0
        self.connections = 0
        self.disconnects = 0
        self.messages = 0
        self.heartbeat_timeouts = 0
        self.message_list = []

    def on_error(self, headers, message):
        log.debug('received an error %s [%s]' % (message, headers))
        self.errors = self.errors + 1

    def on_connecting(self, host_and_port):
        self.connections = self.connections + 1
        log.debug('connecting %s %s (x %s)' % (host_and_port[0], host_and_port[1], self.connections))

    def on_disconnected(self):
        self.disconnects = self.disconnects + 1
        log.debug('disconnected (x %s)' % self.disconnects)

    def on_message(self, headers, message):
        log.debug('received a message %s' % message)
        self.messages = self.messages + 1
        self.message_list.append(message)

    def on_heartbeat_timeout(self):
        log.debug('received heartbeat timeout')
        self.heartbeat_timeouts = self.heartbeat_timeouts + 1


class TestStompServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.frames = []
        
    def start(self):
        log.debug('Starting stomp server')
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.host, self.port))
        self.s.listen(1)
        self.running = True
        thread = threading.Thread(None, self.run)
        thread.daemon = True
        thread.start()
        self.stopped = False
        
    def stop(self):
        if self.conn:
            self.conn.close()
        if self.s:
            try:
                self.s.shutdown(socket.SHUT_WR)
            except Exception:
                log.debug('error shutting down socket')
            self.s.close()
        self.running = False
        self.conn = None
        self.s = None
        log.debug('Connection stopped')
        
    def get_next_frame(self):
        if len(self.frames) > 0:
            rtn = self.frames[0]
            del self.frames[0]
            return rtn
        else:
            return ''

    def add_frame(self, frame):
        self.frames.append(frame)
        
    def run(self):
        self.conn, addr = self.s.accept()
        while self.running:
            try:
                data = self.conn.recv(1024)
                frame = self.get_next_frame()
                if frame is not None:
                    self.conn.send(bytes(frame, 'ascii'))
            except:
                break
        try:
            self.conn.close()
        except:
            pass
        self.stopped = True
        log.debug('Run loop completed')
