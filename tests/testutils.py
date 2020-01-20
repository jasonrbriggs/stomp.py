# -*- coding: utf8 -*-

from configparser import RawConfigParser
import json
import sys
import time
from subprocess import run, PIPE

import pytest

from stomp.utils import *
from stomp import logging

config = RawConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "setup.ini"))

header_re = re.compile(r"[^:]+:.*")
test_text_for_utf8 = "марко"
test_text_for_utf16 = "ǰ捁楴敶免"


def get_environ(name):
    try:
        return os.environ[name]
    except:
        return None


def get_default_host():
    host = config.get("default", "host")
    port = config.get("default", "port")
    return [(get_environ("STD_HOST") or host, int(get_environ("STD_PORT") or port))]


def get_default_vhost():
    try:
        vhost = config.get("default", "vhost")
    except:
        vhost = None
    return get_environ("STD_VHOST") or vhost


def get_default_user():
    user = config.get("default", "user")
    return get_environ("STD_USER") or user


def get_default_password():
    password = config.get("default", "password")
    return get_environ("STD_PASSWORD") or password


def get_ipv6_host():
    if config.has_option("ipv6", "host"):
        host = config.get("ipv6", "host")
    else:
        result = run(["docker", "ps", "-f", "name=stomppy", "--format", "{{.ID}}"], stdout=PIPE)
        container_id = result.stdout.decode("utf-8").rstrip()
        result = run(["docker", "inspect",  container_id], stdout=PIPE)
        j = json.loads(result.stdout.decode("utf-8"))
        j = j[0]
        network = j["NetworkSettings"]
        host = network["GlobalIPv6Address"]
    port = config.get("ipv6", "port")
    return [(get_environ("IPV6_HOST") or host, int(get_environ("IPV6_PORT") or port))]



def get_default_ssl_host():
    host = config.get("default", "host")
    port = config.get("default", "ssl_port")
    return [(get_environ("STD_HOST") or host, int(get_environ("STD_SSL_PORT") or port))]


def get_sni_ssl_host():
    host = config.get("sni", "host")
    port = config.get("sni", "ssl_port")
    return [(get_environ("SNI_HOST") or host, int(get_environ("SNI_SSL_PORT") or port))]


def get_rabbitmq_host():
    host = config.get("rabbitmq", "host")
    port = config.get("rabbitmq", "port")
    return [(get_environ("RABBITMQ_HOST") or host, int(get_environ("RABBITMQ_PORT") or port))]


def get_rabbitmq_user():
    user = config.get("rabbitmq", "user")
    return get_environ("RABBITMQ_USER") or user


def get_rabbitmq_password():
    password = config.get("rabbitmq", "password")
    return get_environ("RABBITMQ_PASSWORD") or password


def get_stompserver_host():
    host = config.get("stompserver", "host")
    port = config.get("stompserver", "port")
    return [(get_environ("STOMPSERVER_HOST") or host, int(get_environ("STOMPSERVER_PORT") or port))]

def get_artemis_host():
    host = config.get("artemis", "host")
    port = config.get("artemis", "port")
    return [(get_environ("ARTEMIS_HOST") or host, int(get_environ("ARTEMIS_PORT") or port))]

def get_artemis_user():
    user = config.get("artemis", "user")
    return get_environ("ARTEMIS_USER") or user

def get_artemis_password():
    password = config.get("artemis", "password")
    return get_environ("ARTEMIS_PASSWORD") or password


class StubStompServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.frames = []

    def start(self):
        logging.info("Starting stomp server")
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.host, self.port))
        self.s.listen(1)
        self.running = True
        thread = threading.Thread(None, self.run)
        thread.daemon = True
        thread.start()
        self.stopped = False
        logging.info("Stomp server started")

    def stop(self):
        logging.info("Stopping test server")
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
        logging.info("Connection stopped")

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
                    logging.info("Stompserver sending frame %s", frame)
                    self.conn.send(encode(frame))
            except Exception:
                _, e, _ = sys.exc_info()
                logging.debug(e)
                break
            time.sleep(0.1)
        try:
            self.conn.close()
        except:
            pass
        self.stopped = True
        logging.info("Run loop completed")


class StubStdin(object):
    pass


class StubStdout(object):
    def __init__(self, test):
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
            pytest.fail("No expectations - actual '%s'" % txt)
            return

        for x in range(0, len(self.expects)):
            chk = self.expects[x]
            if chk.match(txt):
                del self.expects[x]
                return

        pytest.fail("'%s' was not expected (expectations were: [%s])" % (txt, self.expects))

    def flush(self):
        pass


def validate_send(conn, connections=1, messages=1, errors=0):
    listener = conn.get_listener("testlistener")
    listener.wait_on_receipt()
    listener.wait_for_message()

    assert listener.connections == 1, "should have received 1 connection acknowledgement"
    assert listener.messages == 1, "should have received 1 message"
    assert listener.errors == 0, "should not have received any errors"


def is_inside_travis():
    if os.environ.get("TRAVIS", "false") == "true":
        logging.info("Not running test inside travis")
        return True
    return False