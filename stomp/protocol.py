"""Provides the 1.0, 1.1 and 1.2 protocol classes.
"""


import uuid

from stomp.exception import ConnectFailedException
from stomp.listener import *
from stomp.backward import encode
from stomp.constants import *
import stomp.utils as utils


class Protocol10(ConnectionListener):
    """
    Represents version 1.0 of the protocol (see https://stomp.github.io/stomp-specification-1.0.html).
    
    Most users should not instantiate the protocol directly. See :py:mod:`stomp.connect` for connection classes.
    """
    def __init__(self, transport):
        self.transport = transport
        transport.set_listener('protocol-listener', self)
        self.version = '1.0'

    def send_frame(self, cmd, headers={}, body=''):
        """
        Encode and send a stomp frame
        through the underlying transport:
        
        :param cmd: the protocol command
        :param headers: a map of headers to include in the frame
        :param body: the content of the message
        """
        frame = utils.Frame(cmd, headers, body)
        self.transport.transmit(frame)

    def abort(self, transaction, headers={}, **keyword_headers):
        """
        Abort a transaction.
        
        :param transaction: the identifier of the transaction
        :param headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        """
        assert transaction is not None, "'transaction' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_ABORT, headers)

    def ack(self, id, transaction=None):
        """
        Acknowledge 'consumption' of a message by id.
        
        :param id: identifier of the message
        :param transaction: include the acknowledgement in the specified transaction
        """
        assert id is not None, "'id' is required"
        headers = {HDR_MESSAGE_ID : id}
        if transaction:
            headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_ACK, headers)

    def begin(self, transaction=None, headers={}, **keyword_headers):
        """
        Begin a transaction.
        
        :param transaction: the identifier for the transaction (optional - if not specified
            a unique transaction id will be generated)
        :param headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        
        :return: the transaction id
        """
        headers = utils.merge_headers([headers, keyword_headers])
        if not transaction:
            transaction = str(uuid.uuid4())
        headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_BEGIN, headers)
        return transaction

    def commit(self, transaction=None, headers={}, **keyword_headers):
        """
        Commit a transcation.
        
        :param transaction: the identifier for the transaction
        :param headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        """
        assert transaction is not None, "'transaction' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_COMMIT, headers)

    def connect(self, username=None, passcode=None, wait=False, headers={}, **keyword_headers):
        """
        Start a connection.
        
        :param username: the username to connect with
        :param passcode: the password used to authenticate with
        :param wait: if True, wait for the connection to be established/acknowledged
        :param headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        """
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
        """
        Disconnect from the server.
        
        :param receipt: the receipt to use (once the server acknowledges that receipt, we're
            officially disconnected)
        :param headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        """
        headers = utils.merge_headers([headers, keyword_headers])
        if receipt:
            headers[HDR_RECEIPT] = receipt
        self.send_frame(CMD_DISCONNECT, headers)

    def send(self, destination, body, content_type=None, headers={}, suppress_content_length=False, **keyword_headers):
        """
        Send a message to a destination.
        
        :param destination: the destination of the message (e.g. queue or topic name)
        :param body: the content of the message
        :param content_type: the content type of the message
        :param headers: a map of any additional headers the broker requires
        :param suppress_content_length: toggle off sending a content_length header
        :param keyword_headers: any additional headers the broker requires
        """
        assert destination is not None, "'destination' is required"
        assert body is not None, "'body' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_DESTINATION] = destination
        if content_type:
            headers[HDR_CONTENT_TYPE] = content_type
        body = encode(body)
        if not suppress_content_length and body and HDR_CONTENT_LENGTH not in headers:
            headers[HDR_CONTENT_LENGTH] = len(body)
        self.send_frame(CMD_SEND, headers, body)

    def subscribe(self, destination, id=None, ack='auto', headers={}, **keyword_headers):
        """
        Subscribe to a destination.
        
        :param destination: the topic or queue to subscribe to
        :param id: a unique id to represent the subscription
        :param ack: acknowledgement mode, either auto, client, or client-individual 
            (see http://stomp.github.io/stomp-specification-1.2.html#SUBSCRIBE_ack_Header)
            for more information
        :param headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        """
        assert destination is not None, "'destination' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_DESTINATION] = destination
        if id:
            headers[HDR_ID] = id
        headers[HDR_ACK] = ack
        self.send_frame(CMD_SUBSCRIBE, headers)

    def unsubscribe(self, destination=None, id=None, headers={}, **keyword_headers):
        """
        Unsubscribe from a destination by either id or the destination name.
        
        :param destination: the name of the topic or queue to unsubscribe from
        :param id: the unique identifier of the topic or queue to unsubscribe from
        :param headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        """
        assert id is not None or destination is not None, "'id' or 'destination' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        if id:
            headers[HDR_ID] = id
        if destination:
            headers[HDR_DESTINATION] = destination
        self.send_frame(CMD_UNSUBSCRIBE, headers)


class Protocol11(HeartbeatListener, ConnectionListener):
    """
    Represents version 1.1 of the protocol (see https://stomp.github.io/stomp-specification-1.1.html).
    
    Most users should not instantiate the protocol directly. See :py:mod:`stomp.connect` for connection classes.
    """
    def __init__(self, transport, heartbeats=(0, 0)):
        HeartbeatListener.__init__(self, heartbeats)
        self.transport = transport
        transport.set_listener('protocol-listener', self)
        self.version = '1.1'

    def _escape_headers(self, headers):
        for key, val in headers.items():
            try:
                val = val.replace('\\', '\\\\').replace('\n', '\\n').replace(':', '\\c')
            except:
                pass
            headers[key] = val

    def send_frame(self, cmd, headers={}, body=''):
        """
        Encode and send a stomp frame
        through the underlying transport:
        
        :param cmd: the protocol command
        :param headers: a map of headers to include in the frame
        :param body: the content of the message
        """
        if cmd != CMD_CONNECT:
            self._escape_headers(headers)
        frame = utils.Frame(cmd, headers, body)
        self.transport.transmit(frame)

    def abort(self, transaction, headers={}, **keyword_headers):
        """
        Abort a transaction.
        
        :param transaction: the identifier of the transaction
        :param headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        """
        assert transaction is not None, "'transaction' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_ABORT, headers)

    def ack(self, id, subscription, transaction=None):
        """
        Acknowledge 'consumption' of a message by id.
        
        :param id: identifier of the message
        :param transaction: include the acknowledgement in the specified transaction
        """
        assert id is not None, "'id' is required"
        assert subscription is not None, "'subscription' is required"
        headers = { HDR_MESSAGE_ID : id, HDR_SUBSCRIPTION : subscription }
        if transaction:
            headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_ACK, headers)

    def begin(self, transaction=None, headers={}, **keyword_headers):
        """
        Begin a transaction.
        
        :param transaction: the identifier for the transaction (optional - if not specified
            a unique transaction id will be generated)
        :param headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        
        :return: the transaction id
        """
        headers = utils.merge_headers([headers, keyword_headers])
        if not transaction:
            transaction = str(uuid.uuid4())
        headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_BEGIN, headers)
        return transaction

    def commit(self, transaction=None, headers={}, **keyword_headers):
        """
        Commit a transcation.
        
        :param transaction: the identifier for the transaction
        :param headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        """
        assert transaction is not None, "'transaction' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_COMMIT, headers)

    def connect(self, username=None, passcode=None, wait=False, headers={}, **keyword_headers):
        """
        Start a connection.
        
        :param username: the username to connect with
        :param passcode: the password used to authenticate with
        :param wait: if True, wait for the connection to be established/acknowledged
        :param headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        """
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
        """
        Disconnect from the server.
        
        :param receipt: the receipt to use (once the server acknowledges that receipt, we're
            officially disconnected)
        :param headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        """
        headers = utils.merge_headers([headers, keyword_headers])
        if receipt:
            headers[HDR_RECEIPT] = receipt
        self.send_frame(CMD_DISCONNECT, headers)

    def nack(self, id, subscription, transaction=None):
        """
        Let the server know that a message was not consumed.
        
        :param id: the unique id of the message to nack
        :param subscription: the subscription this message is associated with
        :param transaction: include this nack in a named transaction
        :param headers: a map of any additional headers the broker requires
        :param keyword_headers: any additional headers the broker requires
        """
        assert id is not None, "'id' is required"
        assert subscription is not None, "'subscription' is required"
        headers = { HDR_MESSAGE_ID : id, HDR_SUBSCRIPTION : subscription }
        if transaction:
            headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_NACK, headers)

    def send(self, destination, body, content_type=None, headers={}, suppress_content_length=False, **keyword_headers):
        """
        Send a message to a destination in the messaging system (as per https://stomp.github.io/stomp-specification-1.2.html#SEND)
        
        :param destination: the destination (such as a message queue - for example '/queue/test' - or a message topic)
        :param body: the content of the message
        :param content_type: the MIME type of message 
        :param headers: additional headers to send in the message frame
        :param suppress_content_length: toggle off sending a content_length header
        :param keyword_headers: any additional headers the broker requires
        """
        assert destination is not None, "'destination' is required"
        assert body is not None, "'body' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_DESTINATION] = destination
        if content_type:
            headers[HDR_CONTENT_TYPE] = content_type
        body = encode(body)
        if not suppress_content_length and body and HDR_CONTENT_LENGTH not in headers:
            headers[HDR_CONTENT_LENGTH] = len(body)
        self.send_frame(CMD_SEND, headers, body)

    def subscribe(self, destination, id, ack='auto', headers={}, **keyword_headers):
        """
        Subscribe to a destination
        
        :param destination: the topic or queue to subscribe to
        :param id: the identifier to uniquely identify the subscription
        :param ack: either auto, client or client-individual (see https://stomp.github.io/stomp-specification-1.2.html#SUBSCRIBE for more info)
        :param headers: a map of any additional headers to send with the subscription
        :param keyword_headers: any additional headers to send with the subscription
        """
        assert destination is not None, "'destination' is required"
        assert id is not None, "'id' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_DESTINATION] = destination
        headers[HDR_ID] = id
        headers[HDR_ACK] = ack
        self.send_frame(CMD_SUBSCRIBE, headers)

    def unsubscribe(self, id, headers={}, **keyword_headers):
        """
        Unsubscribe from a destination by its unique identifier
        
        :param id: the unique identifier to unsubscribe from
        :param headers: additional headers to send with the unsubscribe
        """
        assert id is not None, "'id' is required"
        headers = utils.merge_headers([headers, keyword_headers])
        headers[HDR_ID] = id
        self.send_frame(CMD_UNSUBSCRIBE, headers)


class Protocol12(Protocol11):
    """
    Represents version 1.2 of the protocol (see https://stomp.github.io/stomp-specification-1.2.html).
    
    Most users should not instantiate the protocol directly. See :py:mod:`stomp.connect` for connection classes.
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
        """
        Acknowledge 'consumption' of a message by id.
        
        :param id: identifier of the message
        :param transaction: include the acknowledgement in the specified transaction
        """
        assert id is not None, "'id' is required"
        headers = { HDR_ID : id }
        if transaction:
            headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_ACK, headers)

    def nack(self, id, transaction=None):
        """
        Let the server know that a message was not consumed.
        
        :param id: the unique id of the message to nack
        :param transaction: include this nack in a named transaction
        """
        assert id is not None, "'id' is required"
        headers = {HDR_ID : id}
        if transaction:
            headers[HDR_TRANSACTION] = transaction
        self.send_frame(CMD_NACK, headers)

    def connect(self, username=None, passcode=None, wait=False, headers={}, **keyword_headers):
        """
        Send a STOMP CONNECT frame. Differs from 1.0 and 1.1 versions in that the HOST header is enforced.
        
        :param username: optionally specify the login user
        :param passcode: optionally specify the user password
        :param wait: wait for the connection to complete before returning
        :param headers: a map of any additional headers to send with the subscription
        :param keyword_headers: any additional headers to send with the subscription
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
