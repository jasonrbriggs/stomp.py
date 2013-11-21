import os
import socket
import sys
import threading
import logging
log = logging.getLogger('testutils.py')

from stomp import ConnectionListener, StatsListener, WaitingListener
from stomp.backward import *


def get_standard_host():
    return [(os.environ['STD_HOST'], int(os.environ['STD_PORT']))]

    
def get_standard_ssl_host():
    return [(os.environ['STD_HOST'], int(os.environ['STD_SSL_PORT']))]


def get_rabbitmq_host():
    return [(os.environ['RABBITMQ_HOST'], int(os.environ['RABBITMQ_PORT']))]
    

def get_stompserver_host():
    return [(os.environ['STOMPSERVER_HOST'], int(os.environ['STOMPSERVER_PORT']))]
    

class TestListener(StatsListener,WaitingListener):
    def __init__(self, receipt=None):
        StatsListener.__init__(self)
        WaitingListener.__init__(self, receipt)
        self.message_list = []
        self.message_condition = threading.Condition()
        self.message_received = False

    def on_message(self, headers, message):
        StatsListener.on_message(self, headers, message)
        self.message_list.append((headers, message))
        self.message_condition.acquire()
        self.message_received = True
        self.message_condition.notify()
        self.message_condition.release()
        
    def wait_for_message(self):
        self.message_condition.acquire()
        while not self.message_received:
            self.message_condition.wait()
        self.message_condition.release()
        self.message_received = False
        
    def get_latest_message(self):
        return self.message_list[len(self.message_list)-1]


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
            try:
                self.conn.shutdown(socket.SHUT_WR)
            except Exception:
                pass
            self.conn.close()
        if self.s:
            self.s.close()
        self.running = False
        self.conn = None
        self.s = None
        self.stopped = True
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
                if self.conn is None:
                    break
                if frame is not None:
                    self.conn.send(encode(frame))
            except Exception:
                _, e, _ = sys.exc_info()
                log.debug(e)
                break
        try:
            self.conn.close()
        except:
            pass
        self.stopped = True
        log.debug('Run loop completed')
