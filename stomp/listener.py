import threading
import time

import exception
import utils
from constants import *

##@namespace stomp.listener
# Various listeners for using with stomp.py connections.


try:
    from fractions import gcd
except ImportError:
    from backward import gcd
    
import logging
log = logging.getLogger('stomp.py')


class ConnectionListener(object):
    """
    This class should be used as a base class for objects registered
    using Connection.set_listener().
    """
    def on_connecting(self, host_and_port):
        """
        Called by the STOMP connection once a TCP/IP connection to the
        STOMP server has been established or re-established. Note that
        at this point, no connection has been established on the STOMP
        protocol level. For this, you need to invoke the "connect"
        method on the connection.

        \param host_and_port
            a tuple containing the host name and port number to which the connection has been established.
        """
        pass

    def on_connected(self, headers, body):
        """
        Called by the STOMP connection when a CONNECTED frame is
        received, that is after a connection has been established or
        re-established.

        \param headers
            a dictionary containing all headers sent by the server as key/value pairs.
        \param body
            the frame's payload. This is usually empty for CONNECTED frames.
        """
        pass

    def on_disconnected(self):
        """
        Called by the STOMP connection when a TCP/IP connection to the
        STOMP server has been lost.  No messages should be sent via
        the connection until it has been reestablished.
        """
        pass
        
    def on_heartbeat_timeout(self):
        """
        Called by the STOMP connection when a heartbeat message has not been
        received beyond the specified period.
        """
        pass
        
    def on_before_message(self, headers, body):
        """
        Called by the STOMP connection before a message is returned to the client app. Returns a tuple
        containing the headers and body (so that implementing listeners can pre-process the content).

        \param headers
            the message headers
        \param body
            the message body
        """
        return (headers, body)

    def on_message(self, headers, body):
        """
        Called by the STOMP connection when a MESSAGE frame is
        received.

        \param headers
            a dictionary containing all headers sent by the server as key/value pairs.
        \param body
            the frame's payload - the message body.
        """
        pass

    def on_receipt(self, headers, body):
        """
        Called by the STOMP connection when a RECEIPT frame is
        received, sent by the server if requested by the client using
        the 'receipt' header.

        \param headers
            a dictionary containing all headers sent by the server as key/value pairs.
        \param body
            the frame's payload. This is usually empty for RECEIPT frames.
        """
        pass

    def on_error(self, headers, body):
        """
        Called by the STOMP connection when an ERROR frame is
        received.

        \param headers
            a dictionary containing all headers sent by the server as key/value pairs.
        \param body
            the frame's payload - usually a detailed error description.
        """
        pass

    def on_send(self, frame):
        """
        Called by the STOMP connection when it is in the process of sending a message
        
        \param frame
            the frame to be sent
        """
        pass

    def on_heartbeat(self):
        """
        Called on receipt of a heartbeat.
        """
        pass


class HeartbeatListener(ConnectionListener):
    """
    Listener used to handle STOMP heartbeating.
    """
    def __init__(self, heartbeats):
        self.connected = False
        self.running = False
        self.heartbeats = heartbeats
        self.__received_heartbeat = time.time()
    
    def on_connected(self, headers, body):
        """
        Once the connection is established, and 'heart-beat' is found in the headers, we calculate the real heartbeat numbers
        (based on what the server sent and what was specified by the client) - if the heartbeats are not 0, we start up the
        heartbeat loop accordingly.
        """
        if 'heart-beat' in headers.keys():
            self.heartbeats = utils.calculate_heartbeats(headers['heart-beat'].replace(' ', '').split(','), self.heartbeats)
            if self.heartbeats != (0,0):
                utils.default_create_thread(self.__heartbeat_loop)
                
    def on_message(self, headers, body):
        """
        Reset the last received time whenever a message is received.
        """
        # reset the heartbeat for any received message
        self.__received_heartbeat = time.time()
        
    def on_heartbeat(self):
        """
        Reset the last received time whenever a heartbeat message is received.
        """
        self.__received_heartbeat = time.time()
        
    def on_send(self, frame):
        """
        Add the heartbeat header to the frame when connecting.
        """
        if frame.cmd == 'CONNECT' or frame.cmd == 'STOMP':
            if self.heartbeats != (0, 0):
                frame.headers[HDR_HEARTBEAT] = '%s,%s' % self.heartbeats
     
    def __heartbeat_loop(self):
        """
        Main loop for sending (and monitoring received) heartbeats.
        """
        send_sleep = self.heartbeats[0] / 1000

        # receive gets an additional threshold of 3 additional seconds
        receive_sleep = (self.heartbeats[1] / 1000) + 3

        if send_sleep == 0:
            sleep_time = receive_sleep
        elif receive_sleep == 0:
            sleep_time = send_sleep
        else:
            # sleep is the GCD of the send and receive times
            sleep_time = gcd(send_sleep, receive_sleep) / 2.0

        send_time = time.time()
        receive_time = time.time()

        while self.running:
            time.sleep(sleep_time)

            now = time.time()

            if now - send_time > send_sleep:
                send_time = now
                log.debug('Sending a heartbeat message at %s' % now)
                try:
                    self.send_frame(utils.Frame(None, {}, None))
                except exception.NotConnectedException:
                    log.debug('Lost connection, unable to send heartbeat')

            diff_receive = now - receive_time
            if diff_receive > receive_sleep:
                diff_heartbeat = now - self.__received_heartbeat
                if diff_heartbeat > receive_sleep:
                    log.debug('Heartbeat timeout: diff_receive=%s, diff_heartbeat=%s, time=%s, lastrec=%s' % (diff_receive, diff_heartbeat, now, self.__received_heartbeat))
                    # heartbeat timeout
                    for listener in self.listeners.values():
                        listener.on_heartbeat_timeout()
                    self.disconnect_socket()
                    self.set_connected(False)


class WaitingListener(ConnectionListener):
    """
    A listener which waits for a specific receipt to arrive
    """
    def __init__(self, receipt):
        self.condition = threading.Condition()
        self.receipt = receipt
        self.received = False
        
    def on_receipt(self, headers, body):
        """
        If the receipt id can be found in the headers, then notify the waiting thread.
        """
        if 'receipt-id' in headers and headers['receipt-id'] == self.receipt:
            self.condition.acquire()
            self.received = True
            self.condition.notify()
            self.condition.release()
        
    def wait_on_receipt(self):
        """
        Wait until we receive a message receipt.
        """
        self.condition.acquire()
        while not self.received:
            self.condition.wait()
        self.condition.release()
        self.received = False


class StatsListener(ConnectionListener):
    """
    A connection listener for recording statistics on messages sent and received.
    """
    def __init__(self):
        ## The number of errors received
        self.errors = 0
        ## The number of connections established
        self.connections = 0
        ## The number of disconnections
        self.disconnects = 0
        ## The number of messages received
        self.messages = 0
        ## The number of messages sent
        self.messages_sent = 0
        ## The number of heartbeat timeouts
        self.heartbeat_timeouts = 0

    def on_disconnected(self):
        """
        Increment the disconnect count.
        \see ConnectionListener::on_disconnected
        """
        self.disconnects = self.disconnects + 1
        log.debug('disconnected (x %s)' % self.disconnects)

    def on_error(self, headers, message):
        """
        Increment the error count.
        \see ConnectionListener::on_error
        """
        log.debug('received an error %s [%s]' % (message, headers))
        self.errors += 1

    def on_connecting(self, host_and_port):
        """
        Increment the connection count.
        \see ConnectionListener::on_connecting
        """
        log.debug('connecting %s %s (x %s)' % (host_and_port[0], host_and_port[1], self.connections))
        self.connections += 1

    def on_message(self, headers, body):
        """
        Increment the message received count.
        \see ConnectionListener::on_message
        """
        log.debug('received a message %s' % body)
        self.messages += 1
        
    def on_send(self, frame):
        """
        Increment the send count.
        \see ConnectionListener::on_send
        """
        self.messages_sent += 1
        
    def on_heartbeat_timeout(self):
        """
        Increment the heartbeat timeout.
        \see ConnectionListener::on_heartbeat_timeout
        """
        log.debug('received heartbeat timeout')
        self.heartbeat_timeouts = self.heartbeat_timeouts + 1

    def __str__(self):
        """
        Return a string containing the current statistics (messages sent and received,
        errors, etc)
        """
        return '''Connections: %s
Messages sent: %s
Messages received: %s
Errors: %s''' % (self.connections, self.messages_sent, self.messages, self.errors)
