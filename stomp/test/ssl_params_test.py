import unittest

from stomp import transport

from testutils import *

class TestSSLParams(unittest.TestCase):
    def setUp(self):
        self.host1 = get_standard_ssl_host()[0]
        self.host2 = get_standard_ssl_host()[0]
        self.transport = transport.Transport(host_and_ports=[
            self.host1,
            self.host2,
        ])
        self.ssl_key_file = 'ssl_key_file'
        self.ssl_cert_file = 'ssl_cert_file'
        self.ssl_ca_certs = 'ssl_ca_certs'
        self.ssl_cert_validator = 'validator'
        self.ssl_version = 'version'

    def test_add_ssl(self):
        self.transport.add_ssl([self.host1],
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
