import pytest

import stomp
from stomp import transport
from stomp.listener import TestListener
from .testutils import *


host1 = get_default_ssl_host()[0]
host2 = get_default_ssl_host()[0]
ssl_key_file = "ssl_key_file"
ssl_cert_file = "ssl_cert_file"
ssl_ca_certs = "ssl_ca_certs"
ssl_cert_validator = "validator"
ssl_version = "version"

@pytest.fixture
def stomp_transport():
    t = transport.Transport(host_and_ports=[host1, host2])
    yield t


class TestSSL(object):
    def test_ssl_connection(self):
        listener = TestListener("123", print_to_log=True)
        try:
            import ssl
            queuename = "/queue/test4-%s" % listener.timestamp
            conn = stomp.Connection(get_default_ssl_host())
            conn.set_ssl(get_default_ssl_host())
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
