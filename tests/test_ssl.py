import importlib
import pytest

import stomp
from stomp.listener import TestListener
from stomp import logging
from .testutils import *


host1 = get_ssl_host()[0]
host2 = get_ssl_host()[0]
ssl_key_file = "ssl_key_file"
ssl_cert_file = "ssl_cert_file"
ssl_ca_certs = "ssl_ca_certs"
ssl_cert_validator = "ssl_cert_validator"
ssl_version = "version"
# Necessary to see the root cause of SSL errors
logging.log_to_stdout(verbose_logging=True)


#@pytest.fixture
#def stomp_transport():
#    t = transport.Transport(host_and_ports=[host1, host2])
#    yield t


class TestSSL(object):
    def test_ssl_connection(self):
        listener = TestListener("123", print_to_log=True)
        try:
            import ssl
            queuename = "/queue/testssl-%s" % listener.timestamp
            conn = stomp.Connection(get_ssl_host(), timeout=5)
            conn.set_ssl(get_ssl_host())
            conn.set_listener("testlistener", listener)
            conn.connect(get_default_user(), get_default_password(), wait=True)
            conn.subscribe(destination=queuename, id=1, ack="auto")

            conn.send(body="this is a test", destination=queuename, receipt="123")

            listener.wait_on_receipt()
            listener.wait_for_message()

            conn.disconnect(receipt=None)

            assert conn.get_ssl() is not None
            assert listener.connections == 1, "should have received 1 connection acknowledgement"
            assert listener.messages == 1, "should have received 1 message"
            assert listener.errors == 0, "should not have received any errors"
        except ImportError:
            pass

    def test_ssl_client_cert_connection(self):
        listener = TestListener("123", print_to_log=True)
        try:
            import ssl
            queuename = "/queue/testsslclient-%s" % listener.timestamp
            conn = stomp.Connection(get_ssl_host())
            conn.set_ssl(get_ssl_host(), key_file='tmp/client.key', cert_file='tmp/client.pem', ca_certs='tmp/broker.pem')
            conn.set_listener("testlistener", listener)
            conn.connect(get_default_user(), get_default_password(), wait=True)
            conn.subscribe(destination=queuename, id=1, ack="auto")

            conn.send(body="this is a test with client cert", destination=queuename, receipt="123")

            listener.wait_on_receipt()
            listener.wait_for_message()

            conn.disconnect(receipt=None)

            assert conn.get_ssl() is not None
            assert listener.connections == 1, "should have received 1 connection acknowledgement"
            assert listener.messages == 1, "should have received 1 message"
            assert listener.errors == 0, "should not have received any errors"
        except ImportError:
            pass

    def test_ssl_invalid_broker_cert_connection(self):
        listener = TestListener("123", print_to_log=True)
        try:
            import ssl
            queuename = "/queue/testsslclient-%s" % listener.timestamp
            conn = stomp.Connection(get_ssl_host(), timeout=5)
            conn.set_ssl(get_ssl_host(), key_file='tmp/client.key', cert_file='tmp/client.pem', ca_certs='tmp/broker2.pem')
            conn.set_listener("testlistener", listener)
            try:
                conn.connect(get_default_user(), get_default_password(), wait=True)
                self.fail("Shouldn't get a successful connection")
            except:
                pass

            assert listener.connections == 0, "should not have received any connection acknowledgements"
            assert listener.messages == 0, "should not have received any messages"
            assert listener.errors == 0, "should not have received any errors"
        except ImportError:
            pass

    def test_ssl_expired_broker_cert_connection(self):
        listener = TestListener("123", print_to_log=True)
        try:
            import ssl
            queuename = "/queue/testsslexpired-%s" % listener.timestamp
            conn = stomp.Connection(get_expired_ssl_host())
            conn.set_ssl(get_expired_ssl_host(), ca_certs='tmp/expiredbroker.pem')
            conn.set_listener("testlistener", listener)
            try:
                conn.connect(get_default_user(), get_default_password(), wait=True)
                pytest.fail("Shouldn't get a successful connection")
            except:
                pass

            assert listener.connections == 0, "should not have received any connection acknowledgements"
            assert listener.messages == 0, "should not have received any messages"
            assert listener.errors == 0, "should not have received any errors"
        except ImportError:
            pass


class TestSSLFailure(object):
    @pytest.mark.run(order=-1)
    def test_ssl_failure(self, monkeypatch):
        import ssl
        monkeypatch.delattr(ssl, "PROTOCOL_TLS_CLIENT", raising=True)
        import stomp.connect as c
        importlib.reload(c)
        assert c.DEFAULT_SSL_VERSION is None
        monkeypatch.undo()
        importlib.reload(ssl)

    @pytest.mark.run(order=-1)
    def test_socket_failure(self, monkeypatch):
        import socket
        monkeypatch.delattr(socket, "SOL_TCP", raising=True)
        monkeypatch.delattr(socket, "SO_KEEPALIVE", raising=True)
        import stomp.connect as c
        importlib.reload(c)
        assert not c.LINUX_KEEPALIVE_AVAIL
        monkeypatch.undo()
        importlib.reload(socket)
