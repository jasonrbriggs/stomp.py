import importlib
import pytest

import stomp
from stomp import transport
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


@pytest.fixture
def stomp_transport():
    t = transport.Transport(host_and_ports=[host1, host2])
    yield t


class TestSSL(object):
    def test_ssl_connection(self):
        listener = TestListener("123", print_to_log=True)
        try:
            import ssl
            queuename = "/queue/testssl-%s" % listener.timestamp
            conn = stomp.Connection(get_ssl_host())
            #conn.set_ssl(get_ssl_host())
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
            conn = stomp.Connection(get_ssl_host())
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

    def test_ssl_connection_non_default_ssl_version(self):
        """
        Tests that when setting the ssl_version in the ssl config, this option
        makes it all the way to the initialized ssl configuration on the socket
        """
        listener = TestListener("123", print_to_log=True)
        try:
            import ssl
            conn = stomp.Connection(get_ssl_host())

            # Ensure that we set a non-default ssl version
            ssl_config = get_ssl_host()
            assert len(ssl_config) == 1
            if stomp.transport.DEFAULT_SSL_VERSION != ssl.PROTOCOL_TLSv1_2:
                ssl_version = ssl.PROTOCOL_TLSv1_2
            else:
                ssl_version = ssl.PROTOCOL_TLSv1_1
            conn.set_ssl(get_ssl_host(), ssl_version=ssl_version)
            conn.set_listener("testlistener", listener)
            conn.connect(get_default_user(), get_default_password(), wait=True)
            assert conn.transport.socket._sslobj.context.protocol == ssl_version
        except ImportError:
            pass

class TestSSLParams(object):
    def test_set_ssl(self, stomp_transport):
        stomp_transport.set_ssl([host1],
                                ssl_key_file,
                                ssl_cert_file,
                                ssl_ca_certs,
                                ssl_cert_validator,
                                ssl_version)
        assert stomp_transport._Transport__ssl_params[host1]["key_file"] == ssl_key_file
        assert stomp_transport._Transport__ssl_params[host1]["cert_file"] == ssl_cert_file
        assert stomp_transport._Transport__ssl_params[host1]["ca_certs"] == ssl_ca_certs
        assert stomp_transport._Transport__ssl_params[host1]["cert_validator"] == ssl_cert_validator
        assert stomp_transport._Transport__ssl_params[host1]["ssl_version"] == ssl_version

    def test_init_ssl_params(self):
        trans = transport.Transport(host_and_ports=[host1, host2])
        trans.set_ssl([host1, host2], ssl_key_file, ssl_cert_file, ssl_ca_certs, ssl_cert_validator, ssl_version)

        for host_port in [host1, host2]:
            assert trans._Transport__ssl_params[host_port]["key_file"] == ssl_key_file
            assert trans._Transport__ssl_params[host_port]["cert_file"] == ssl_cert_file
            assert trans._Transport__ssl_params[host_port]["ca_certs"] == ssl_ca_certs
            assert trans._Transport__ssl_params[host_port]["cert_validator"] == ssl_cert_validator
            assert trans._Transport__ssl_params[host_port]["ssl_version"] == ssl_version


class TestSSLFailure(object):
    @pytest.mark.run(order=-1)
    def test_ssl_failure(self, monkeypatch):
        import ssl
        monkeypatch.delattr(ssl, "PROTOCOL_TLS_CLIENT", raising=True)
        import stomp.transport as t
        importlib.reload(t)
        assert t.DEFAULT_SSL_VERSION is None
        monkeypatch.undo()
        importlib.reload(ssl)

    @pytest.mark.run(order=-1)
    def test_socket_failure(self, monkeypatch):
        import socket
        monkeypatch.delattr(socket, "SOL_TCP", raising=True)
        monkeypatch.delattr(socket, "SO_KEEPALIVE", raising=True)
        import stomp.transport as t
        importlib.reload(t)
        assert not t.LINUX_KEEPALIVE_AVAIL
        monkeypatch.undo()
        importlib.reload(socket)
