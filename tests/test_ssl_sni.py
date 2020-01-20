import pytest

import stomp
from stomp.listener import TestListener
from .testutils import *


class TestSNIMQSend(object):
    """
    To test SNI:

    - Start the docker container

    - Add a couple fully qualified hostnames to your /etc/hosts
        # SNI test hosts
        172.17.0.2 my.example.com
        172.17.0.2 my.example.org

    Connections with SNI to "my.example.com" will be routed to the STOMP server on port 62613.
    Connections without SNI won't be routed.

    """

    def testconnect(self):
        if not is_inside_travis():
            logging.info("Running ipv6 test")
            receipt_id = str(uuid.uuid4())
            conn = stomp.Connection11(get_sni_ssl_host())
            conn.set_ssl(get_sni_ssl_host())
            listener = TestListener(receipt_id, print_to_log=True)
            conn.set_listener('', listener)
            conn.connect(get_default_user(), get_default_password(), wait=True)
            conn.subscribe(destination="/queue/test", id=1, ack="auto")

            logging.info("sending message with receipt %s" % receipt_id)
            conn.send(body="this is a test", destination="/queue/test", receipt=receipt_id)

            listener.wait_for_message()
            conn.disconnect(receipt=None)

            assert listener.connections == 1, "should have received 1 connection acknowledgement"
            assert listener.messages >= 1, "should have received 1 message"
            assert listener.errors == 0, "should not have received any errors"
