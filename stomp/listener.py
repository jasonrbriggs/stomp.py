import threading
import time

import exception
import utils
from constants import *

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

        \param host_and_port a tuple containing the host name and port
        number to which the connection has been established.
        """
        pass

    def on_connected(self, headers, body):
        """
        Called by the STOMP connection when a CONNECTED frame is
        received, that is after a connection has been established or
        re-established.

        \param headers a dictionary containing all headers sent by the
        server as key/value pairs.

        \param body the frame's payload. This is usually empty for
        CONNECTED frames.
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
        return (headers, body)

    def on_message(self, headers, body):
        """
        Called by the STOMP connection when a MESSAGE frame is
        received.

        \param headers a dictionary containing all headers sent by the
        server as key/value pairs.

        \param body the frame's payload - the message body.
        """
        pass

    def on_receipt(self, headers, body):
        """
        Called by the STOMP connection when a RECEIPT frame is
        received, sent by the server if requested by the client using
        the 'receipt' header.

        \param headers a dictionary containing all headers sent by the
        server as key/value pairs.

        \param body the frame's payload. This is usually empty for
        RECEIPT frames.
        """
        pass

    def on_error(self, headers, body):
        """
        Called by the STOMP connection when an ERROR frame is
        received.

        \param headers a dictionary containing all headers sent by the
        server as key/value pairs.

        \param body the frame's payload - usually a detailed error
        description.
        """
        pass

    def on_send(self, frame):
        """
        Called by the STOMP connection when it is in the process of sending a message
        
        \param frame the frame to be sent
        """
        pass

    def on_heartbeat(self):
        """
        Called on receipt of a heartbeat.
        """
        pass


class HeartbeatListener(ConnectionListener):
    def __init__(self, heartbeats):
        self.connected = False
        self.running = False
        self.heartbeats = heartbeats
        self.__received_heartbeat = time.time()
    
    def on_connected(self, headers, body):
        if 'heart-beat' in headers.keys():
            self.heartbeats = utils.calculate_heartbeats(headers['heart-beat'].replace(' ', '').split(','), self.heartbeats)
            if self.heartbeats != (0,0):
                utils.default_create_thread(self.__heartbeat_loop)
                
    def on_message(self, headers, body):
        # reset the heartbeat for any received message
        self.__received_heartbeat = time.time()
        
    def on_heartbeat(self):
        self.__received_heartbeat = time.time()
        
    def on_send(self, frame):
        if frame.cmd == 'CONNECT' or frame.cmd == 'STOMP':
            if self.heartbeats != (0, 0):
                frame.headers[HDR_HEARTBEAT] = '%s,%s' % self.heartbeats
     
    def __heartbeat_loop(self):
        """
        Loop for sending (and monitoring received) heartbeats
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
        if 'receipt-id' in headers and headers['receipt-id'] == self.receipt:
            self.condition.acquire()
            self.received = True
            self.condition.notify()
            self.condition.release()
        
    def wait_on_receipt(self):
        self.condition.acquire()
        while not self.received:
            self.condition.wait()
        self.condition.release()


class StatsListener(ConnectionListener):
    """
    A connection listener for recording statistics on messages sent and received.
    """
    def __init__(self):
        self.errors = 0
        self.connections = 0
        self.messages_recd = 0
        self.messages_sent = 0

    def on_error(self, headers, message):
        """
        \see ConnectionListener::on_error
        """
        self.errors += 1

    def on_connecting(self, host_and_port):
        """
        \see ConnectionListener::on_connecting
        """
        self.connections += 1

    def on_message(self, headers, body):
        """
        \see ConnectionListener::on_message
        """
        self.messages_recd += 1
        
    def on_send(self, frame):
        """
        \see ConnectionListener::on_send
        """
        self.messages_sent += 1
        
    def __str__(self):
        """
        Return a string containing the current statistics (messages sent and received,
        errors, etc)
        """
        return '''Connections: %s
Messages sent: %s
Messages received: %s
Errors: %s''' % (self.connections, self.messages_sent, self.messages_recd, self.errors)
