import uuid

from stomp.exception import ConnectFailedException
from stomp.listener import *
from stomp.backward import encode
from stomp.constants import *
import stomp.utils as utils


##@namespace stomp.protocol
# Provides the 1.0, 1.1 and 1.2 protocol classes.


class Protocol10(ConnectionListener):
    """
    Version 1.0 of the protocol.
    """
    def __init__(self, transport):
        self.transport = transport
        transport.set_listener('protocol-listener', self)
        self.version = '1.0'

    def send_frame(self, cmd, headers={}, body=''):
        frame = utils.Frame(cmd, headers, body)
        self.transport.transmit(frame)

    def abort(self, transaction, headers={}, **keyword_headers):
        assert transaction is not None, "'transaction' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_ABORT, headers)

    def ack(self, id, transaction=None):
        assert id is not None, "'id' is required"
        headers = { HDR_MESSAGE_ID : id }
        if transaction:
            headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_ACK, headers)

    def begin(self, transaction=None, headers={}, **keyword_headers):
        headers = utils.merge_headers([headers, keyword_headers])
        if not transaction:
            transaction = str(uuid.uuid4())
        headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_BEGIN, headers)
        return transaction

    def commit(self, transaction=None, headers={}, **keyword_headers):
        assert transaction is not None, "'transaction' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_TRANSACTION] = transaction
        self.send_frame('COMMIT', headers)

    def connect(self, username=None, passcode=None, wait=False, headers={}, **keyword_headers):
        cmd = CMD_CONNECT
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_ACCEPT_VERSION] = self.version

        if username is not None:
            headers[HDR_LOGIN] = username

        if passcode is not None:
            headers[HDR_PASSCODE] = passcode

        self.send_frame(cmd, headers)

        if wait:
            self.transport.wait_for_connection()
            if self.transport.connection_error:
                raise ConnectFailedException()

    def disconnect(self, receipt=str(uuid.uuid4()), headers={}, **keyword_headers):
        headers = utils.merge_headers([headers, keyword_headers])
        if receipt:
            headers[HDR_RECEIPT] = receipt
        self.send_frame(CMD_DISCONNECT, headers)

    def send(self, destination, body, content_type=None, headers={}, **keyword_headers):
        assert destination is not None, "'destination' is required"
        assert body is not None, "'body' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_DESTINATION] = destination
        if content_type:
            headers[HDR_CONTENT_TYPE] = content_type
        body = encode(body)
        if body and HDR_CONTENT_LENGTH not in headers:
            headers[HDR_CONTENT_LENGTH] = len(body)
        self.send_frame(CMD_SEND, headers, body)

    def subscribe(self, destination, id=None, ack='auto', headers={}, **keyword_headers):
        assert destination is not None, "'destination' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_DESTINATION] = destination
        if id:
            headers[HDR_ID] = id
        headers[HDR_ACK] = ack
        self.send_frame(CMD_SUBSCRIBE, headers)

    def unsubscribe(self, destination=None, id=None, headers={}, **keyword_headers):
        assert id is not None or destination is not None, "'id' or 'destination' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        if id:
            headers[HDR_ID] = id
        if destination:
            headers[HDR_DESTINATION] = destination
        self.send_frame(CMD_UNSUBSCRIBE, headers)


class Protocol11(HeartbeatListener, ConnectionListener):
    """
    Version 1.1 of the protocol.
    """
    def __init__(self, transport, heartbeats=(0, 0)):
        HeartbeatListener.__init__(self, heartbeats)
        self.transport = transport
        transport.set_listener('protocol-listener', self)
        self.version = '1.1'

    def _escape_headers(self, headers):
        for key,val in headers.items():
            try:
                val = val.replace('\\', '\\\\').replace('\n', '\\n').replace(':', '\\c')
            except: pass
            headers[key] = val

    def send_frame(self, cmd, headers={}, body=''):
        if cmd != CMD_CONNECT:
            self._escape_headers(headers)
        frame = utils.Frame(cmd, headers, body)
        self.transport.transmit(frame)

    def abort(self, transaction, headers={}, **keyword_headers):
        assert transaction is not None, "'transaction' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_ABORT, headers)

    def ack(self, id, subscription, transaction=None):
        assert id is not None, "'id' is required"
        assert subscription is not None, "'subscription' is required"
        headers = { HDR_MESSAGE_ID : id, HDR_SUBSCRIPTION : subscription }
        if transaction:
            headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_ACK, headers)

    def begin(self, transaction=None, headers={}, **keyword_headers):
        headers = utils.merge_headers([headers, keyword_headers])
        if not transaction:
            transaction = str(uuid.uuid4())
        headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_BEGIN, headers)
        return transaction

    def commit(self, transaction=None, headers={}, **keyword_headers):
        assert transaction is not None, "'transaction' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_TRANSACTION] = transaction
        self.send_frame('COMMIT', headers)

    def connect(self, username=None, passcode=None, wait=False, headers={}, **keyword_headers):
        cmd = CMD_STOMP
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_ACCEPT_VERSION] = self.version

        if self.transport.vhost:
            headers[HDR_HOST] = self.transport.vhost

        if username is not None:
            headers[HDR_LOGIN] = username

        if passcode is not None:
            headers[HDR_PASSCODE] = passcode

        self.send_frame(cmd, headers)

        if wait:
            self.transport.wait_for_connection()
            if self.transport.connection_error:
                raise ConnectFailedException()

    def disconnect(self, receipt=str(uuid.uuid4()), headers={}, **keyword_headers):
        headers = utils.merge_headers([headers, keyword_headers])
        if receipt:
            headers[HDR_RECEIPT] = receipt
        self.send_frame(CMD_DISCONNECT, headers)

    def nack(self, id, subscription, transaction=None):
        assert id is not None, "'id' is required"
        assert subscription is not None, "'subscription' is required"
        headers = { HDR_MESSAGE_ID : id, HDR_SUBSCRIPTION : subscription }
        if transaction:
            headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_NACK, headers)

    def send(self, destination, body, content_type=None, headers={}, **keyword_headers):
        assert destination is not None, "'destination' is required"
        assert body is not None, "'body' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_DESTINATION] = destination
        if content_type:
            headers[HDR_CONTENT_TYPE] = content_type
        body = encode(body)
        if body and HDR_CONTENT_LENGTH not in headers:
            headers[HDR_CONTENT_LENGTH] = len(body)
        self.send_frame(CMD_SEND, headers, body)

    def subscribe(self, destination, id, ack='auto', headers={}, **keyword_headers):
        assert destination is not None, "'destination' is required"
        assert id is not None, "'id' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_DESTINATION] = destination
        headers[HDR_ID] = id
        headers[HDR_ACK] = ack
        self.send_frame(CMD_SUBSCRIBE, headers)

    def unsubscribe(self, id, headers={}, **keyword_headers):
        assert id is not None, "'id' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_ID] = id
        self.send_frame(CMD_UNSUBSCRIBE, headers)


class Protocol12(Protocol11):
    """
    Version 1.2 of the protocol.
    """
    def __init__(self, transport, heartbeats=(0, 0)):
        Protocol11.__init__(self, transport, heartbeats)
        self.version = '1.2'

    def _escape_headers(self, headers):
        for key,val in headers.items():
            try:
                val = val.replace('\\', '\\\\').replace('\n', '\\n').replace(':', '\\c').replace('\r', '\\r')
            except: pass
            headers[key] = val

    def ack(self, id, transaction=None):
        assert id is not None, "'id' is required"
        headers = { HDR_ID : id }
        if transaction:
            headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_ACK, headers)

    def nack(self, id, transaction=None):
        assert id is not None, "'id' is required"
        headers = { HDR_ID : id }
        if transaction:
            headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_NACK, headers)

    def connect(self, username=None, passcode=None, wait=False, headers={}, **keyword_headers):
        """
        Send a STOMP CONNECT frame. Differs from 1.0 and 1.1 versions in that the HOST header is enforced.
        \param username
            optionally specify the login user
        \param passcode
            optionally specify the user password
        \param wait
            wait for the connection to complete before returning
        """
        cmd = CMD_STOMP
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_ACCEPT_VERSION] = self.version
        headers[HDR_HOST] = self.transport.current_host_and_port[0]

        if self.transport.vhost:
            headers[HDR_HOST] = self.transport.vhost

        if username is not None:
            headers[HDR_LOGIN] = username

        if passcode is not None:
            headers[HDR_PASSCODE] = passcode

        self.send_frame(cmd, headers)

        if wait:
            self.transport.wait_for_connection()
            if self.transport.connection_error:
                raise ConnectFailedException()
