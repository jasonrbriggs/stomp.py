import time
import unittest

import stomp
from stomp import transport
from stomp.listener import TestListener
from stomp.test.testutils import *


class TestSSL(unittest.TestCase):
    def setUp(self):
        listener = TestListener('123')
        self.listener = listener
        self.timestamp = time.strftime('%Y%m%d%H%M%S')

    def test_ssl_connection(self):
        try:
            import ssl
            queuename = '/queue/test4-%s' % self.timestamp
            conn = stomp.Connection(get_default_ssl_host())
            conn.set_ssl(get_default_ssl_host())
            conn.set_listener('', self.listener)
            conn.start()
            conn.connect('admin', 'password', wait=True)
            conn.subscribe(destination=queuename, id=1, ack='auto')

            conn.send(body='this is a test', destination=queuename, receipt='123')

            self.listener.wait_on_receipt()
            conn.disconnect(receipt=None)

            self.assertTrue(self.listener.connections == 1, 'should have received 1 connection acknowledgement')
            self.assertTrue(self.listener.messages == 1, 'should have received 1 message')
            self.assertTrue(self.listener.errors == 0, 'should not have received any errors')
        except ImportError:
            pass


class TestSSLParams(unittest.TestCase):
    def setUp(self):
        self.host1 = get_default_ssl_host()[0]
        self.host2 = get_default_ssl_host()[0]
        self.transport = transport.Transport(host_and_ports=[
            self.host1,
            self.host2,
        ])
        self.ssl_key_file = 'ssl_key_file'
        self.ssl_cert_file = 'ssl_cert_file'
        self.ssl_ca_certs = 'ssl_ca_certs'
        self.ssl_cert_validator = 'validator'
        self.ssl_version = 'version'

    def test_set_ssl(self):
        self.transport.set_ssl([self.host1],
                               self.ssl_key_file,
                               self.ssl_cert_file,
                               self.ssl_ca_certs,
                               self.ssl_cert_validator,
                               self.ssl_version)
        self.assertEqual(
            self.transport._Transport__ssl_params[self.host1]['key_file'],
            self.ssl_key_file,
        )
        self.assertEqual(
            self.transport._Transport__ssl_params[self.host1]['cert_file'],
            self.ssl_cert_file,
        )
        self.assertEqual(
            self.transport._Transport__ssl_params[self.host1]['ca_certs'],
            self.ssl_ca_certs,
        )
        self.assertEqual(
            self.transport._Transport__ssl_params[self.host1]['cert_validator'],
            self.ssl_cert_validator,
        )
        self.assertEqual(
            self.transport._Transport__ssl_params[self.host1]['ssl_version'],
            self.ssl_version,
        )

    def test_init_ssl_params(self):
        trans = transport.Transport(
            use_ssl=True,
            ssl_key_file=self.ssl_key_file,
            ssl_cert_file=self.ssl_cert_file,
            ssl_ca_certs=self.ssl_ca_certs,
            ssl_cert_validator=self.ssl_cert_validator,
            ssl_version=self.ssl_version,
            host_and_ports=[
                self.host1,
                self.host2,
            ])
        for host_port in [self.host1, self.host2]:
            self.assertEqual(
                trans._Transport__ssl_params[host_port]['key_file'],
                self.ssl_key_file,
            )
            self.assertEqual(
                trans._Transport__ssl_params[host_port]['cert_file'],
                self.ssl_cert_file,
            )
            self.assertEqual(
                trans._Transport__ssl_params[host_port]['ca_certs'],
                self.ssl_ca_certs,
            )
            self.assertEqual(
                trans._Transport__ssl_params[host_port]['cert_validator'],
                self.ssl_cert_validator,
            )
            self.assertEqual(
                trans._Transport__ssl_params[host_port]['ssl_version'],
                self.ssl_version,
            )
