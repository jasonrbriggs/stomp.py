import os
import threading
import logging
log = logging.getLogger('testutils.py')

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser


from stomp import StatsListener, WaitingListener
from stomp.backward import *


config = ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'setup.ini'))


def get_environ(name):
    try:
        return os.environ[name]
    except:
        return None

def get_standard_host():
    host = config.get('default', 'host')
    port = config.get('default', 'port')
    return [(get_environ('STD_HOST') or host, int(get_environ('STD_PORT') or port))]

    
def get_standard_ssl_host():
    host = config.get('default', 'host')
    port = config.get('default', 'ssl_port')
    return [(get_environ('STD_HOST') or host, int(get_environ('STD_SSL_PORT') or port))]


def get_rabbitmq_host():
    host = config.get('rabbitmq', 'host')
    port = config.get('rabbitmq', 'port')
    return [(get_environ('RABBITMQ_HOST') or host, int(get_environ('RABBITMQ_PORT') or port))]
    

def get_stompserver_host():
    host = config.get('stompserver', 'host')
    port = config.get('stompserver', 'port')
    return [(get_environ('STOMPSERVER_HOST') or host, int(get_environ('STOMPSERVER_PORT') or port))]
    

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
        log.debug('Stomp server started')
        
    def stop(self):
        log.debug('Stopping test server')
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
