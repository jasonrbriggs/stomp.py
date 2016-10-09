import unittest

import stomp
from stomp.listener import TestListener
from stomp.test.testutils import *


class TestSNIMQSend(unittest.TestCase):
    """
    To test SNI:

    - Run a STOMP server in 127.0.0.1:61613

    - Add a couple fully qualified hostnames to your /etc/hosts
        # SNI test hosts
        127.0.0.1 my.example.com
        127.0.0.1 my.example.org

    - Make a pair of self-signed SSL certificates
        openssl req -x509 -newkey rsa:2048 -keyout key1.pem -out cert1.pem -days 365 -nodes -subj "/CN=my.example.org"
        openssl req -x509 -newkey rsa:2048 -keyout key2.pem -out cert2.pem -days 365 -nodes -subj "/CN=my.example.com"
        cat cert1.pem key1.pem > myorg.pem
        cat cert2.pem key2.pem > mycom.pem

    - Run `haproxy` with a configuration that routes based on the SNI
        defaults
          mode tcp
          option tcplog

        frontend ft_test
          bind 0.0.0.0:65001 ssl crt ./myorg.pem crt ./mycom.pem no-sslv3 no-tls-tickets
          use_backend bk_com_cert if { ssl_fc_sni my.example.com }
          use_backend bk_org_cert if { ssl_fc_sni my.example.org }

        backend bk_com_cert
          server srv1 127.0.0.1:61613

        backend bk_org_cert
          server srv2 127.0.0.1:61614

    Connections with SNI to "my.example.com" will be routed to the STOMP server on port 61613.
    Connections without SNI won't be routed.

    """

    def setUp(self):
        pass

    def testconnect(self):
        conn = stomp.Connection11(get_sni_ssl_host())
        conn.set_ssl(get_sni_ssl_host())
        listener = TestListener('123')
        conn.set_listener('', listener)
        conn.start()
        conn.connect(get_default_user(), get_default_password(), wait=True)
        conn.subscribe(destination='/queue/test', id=1, ack='auto')

        conn.send(body='this is a test', destination='/queue/test', receipt='123')

        listener.wait_on_receipt()
        conn.disconnect(receipt=None)

        self.assertTrue(listener.connections == 1, 'should have received 1 connection acknowledgement')
        self.assertTrue(listener.messages == 1, 'should have received 1 message')
        self.assertTrue(listener.errors == 0, 'should not have received any errors')
