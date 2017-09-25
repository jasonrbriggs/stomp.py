try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser
import logging
import os
import re
import socket
import threading

from stomp.backward import *


log = logging.getLogger('testutils.py')

config = RawConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'setup.ini'))

header_re = re.compile(r'[^:]+:.*')


def get_environ(name):
    try:
        return os.environ[name]
    except:
        return None


def get_default_host():
    host = config.get('default', 'host')
    port = config.get('default', 'port')
    return [(get_environ('STD_HOST') or host, int(get_environ('STD_PORT') or port))]


def get_default_vhost():
    try:
        vhost = config.get('default', 'vhost')
    except:
        vhost = None
    return get_environ('STD_VHOST') or vhost


def get_default_user():
    user = config.get('default', 'user')
    return get_environ('STD_USER') or user


def get_default_password():
    password = config.get('default', 'password')
    return get_environ('STD_PASSWORD') or password


def get_ipv6_host():
    host = config.get('ipv6', 'host')
    port = config.get('ipv6', 'port')
    return [(get_environ('IPV6_HOST') or host, int(get_environ('IPV6_PORT') or port))]


def get_default_ssl_host():
    host = config.get('default', 'host')
    port = config.get('default', 'ssl_port')
    return [(get_environ('STD_HOST') or host, int(get_environ('STD_SSL_PORT') or port))]


def get_sni_ssl_host():
    host = config.get('sni', 'host')
    port = config.get('sni', 'ssl_port')
    return [(get_environ('SNI_HOST') or host, int(get_environ('SNI_SSL_PORT') or port))]


def get_rabbitmq_host():
    host = config.get('rabbitmq', 'host')
    port = config.get('rabbitmq', 'port')
    return [(get_environ('RABBITMQ_HOST') or host, int(get_environ('RABBITMQ_PORT') or port))]


def get_rabbitmq_user():
    user = config.get('rabbitmq', 'user')
    return get_environ('RABBITMQ_USER') or user


def get_rabbitmq_password():
    password = config.get('rabbitmq', 'password')
    return get_environ('RABBITMQ_PASSWORD') or password


def get_stompserver_host():
    host = config.get('stompserver', 'host')
    port = config.get('stompserver', 'port')
    return [(get_environ('STOMPSERVER_HOST') or host, int(get_environ('STOMPSERVER_PORT') or port))]


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
        self.conn, _ = self.s.accept()
        while self.running:
            try:
                _ = self.conn.recv(1024)
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


class TestStdin(object):
    pass


class TestStdout(object):
    def __init__(self, test):
        self.test = test
        self.expects = []

    def expect(self, txt):
        self.expects.insert(0, re.compile(txt))

    def write(self, txt):
        txt = txt.rstrip()
        if txt != '':
            print(txt)
        if txt == '>' or txt == '' or header_re.match(txt):
            return
        if len(self.expects) == 0:
            self.test.fail('No expectations - actual "%s"' % txt)
            return

        for x in range(0, len(self.expects)):
            chk = self.expects[x]
            if chk.match(txt):
                del self.expects[x]
                return

        self.test.fail('"%s" was not expected' % txt)

    def flush(self):
        pass
