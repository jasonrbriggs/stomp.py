"""Various listeners for using with stomp.py connections.
"""

import sys
import threading
import time
from time import monotonic

import stomp.exception as exception
import stomp.utils as utils
from stomp.constants import *
from stomp import logging


class Publisher(object):
    """
    Simply a registry of listeners.
    """

    def set_listener(self, name, listener):
        """
        Set a named listener to use with this connection. See :py:class:`stomp.listener.ConnectionListener`

        :param str name: the name of the listener
        :param ConnectionListener listener: the listener object
        """
        pass

    def remove_listener(self, name):
        """
        Remove a listener.

        :param str name: the name of the listener to remove
        """
        pass

    def get_listener(self, name):
        """
        Return the named listener.

        :param str name: the listener to return

        :rtype: ConnectionListener
        """
        return None


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

        :param (str,int) host_and_port: a tuple containing the host name and port number to which the connection
            has been established.
        """
        pass

    def on_connected(self, frame):
        """
        Called by the STOMP connection when a CONNECTED frame is
        received (after a connection has been established or
        re-established).

        :param Frame frame: the stomp frame
        """
        pass

    def on_disconnecting(self):
        """
        Called before a DISCONNECT frame is sent.
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

    def on_before_message(self, frame):
        """
        Called by the STOMP connection before a message is returned to the client app. Returns a tuple
        containing the headers and body (so that implementing listeners can pre-process the content).

        :param Frame frame: the stomp frame
        """
        pass

    def on_message(self, frame):
        """
        Called by the STOMP connection when a MESSAGE frame is received.

        :param Frame frame: the stomp frame
        """
        pass

    def on_receipt(self, frame):
        """
        Called by the STOMP connection when a RECEIPT frame is
        received, sent by the server if requested by the client using
        the 'receipt' header.

        :param Frame frame: the stomp frame
        """
        pass

    def on_error(self, frame):
        """
        Called by the STOMP connection when an ERROR frame is received.

        :param Frame frame: the stomp frame
        """
        pass

    def on_send(self, frame):
        """
        Called by the STOMP connection when it is in the process of sending a message

        :param Frame frame: the stomp frame
        """
        pass

    def on_heartbeat(self):
        """
        Called on receipt of a heartbeat.
        """
        pass

    def on_receiver_loop_completed(self, frame):
        """
        Called when the connection receiver_loop has finished.
        """
        pass


class HeartbeatListener(ConnectionListener):
    """
    Listener used to handle STOMP heartbeating.
    """
    def __init__(self, transport, heartbeats, heart_beat_receive_scale=1.5):
        self.running = False
        self.transport = transport
        self.heartbeats = heartbeats
        self.received_heartbeat = None
        self.heartbeat_thread = None
        self.next_outbound_heartbeat = None
        self.heart_beat_receive_scale = heart_beat_receive_scale
        self.heartbeat_terminate_event = threading.Event()
        self.disconnecting = False

    def on_connected(self, frame):
        """
        Once the connection is established, and 'heart-beat' is found in the headers, we calculate the real
        heartbeat numbers (based on what the server sent and what was specified by the client) - if the heartbeats
        are not 0, we start up the heartbeat loop accordingly.

        :param Frame frame: the stomp frame
        """
        self.disconnecting = False
        if "heart-beat" in frame.headers:
            self.heartbeats = utils.calculate_heartbeats(
                frame.headers["heart-beat"].replace(" ", "").split(","), self.heartbeats)
            logging.debug("heartbeats calculated %s", str(self.heartbeats))
            if self.heartbeats != (0, 0):
                self.send_sleep = self.heartbeats[0] / 1000

                # by default, receive gets an additional grace of 50%
                # set a different heart-beat-receive-scale when creating the connection to override that
                self.receive_sleep = (self.heartbeats[1] / 1000) * self.heart_beat_receive_scale

                logging.debug("set receive_sleep to %s, send_sleep to %s", self.receive_sleep, self.send_sleep)

                # Give grace of receiving the first heartbeat
                self.received_heartbeat = monotonic() + self.receive_sleep

                self.running = True
                if self.heartbeat_thread is None:
                    self.heartbeat_terminate_event.clear()
                    self.heartbeat_thread = utils.default_create_thread(
                        self.__heartbeat_loop)
                    self.heartbeat_thread.name = "StompHeartbeat%s" % \
                        getattr(self.heartbeat_thread, "name", "Thread")

    def on_disconnected(self):
        self.running = False
        self.heartbeat_terminate_event.set()

    def on_disconnecting(self):
        self.disconnecting = True

    def on_message(self, frame):
        """
        Reset the last received time whenever a message is received.

        :param Frame frame: the stomp frame
        """
        # reset the heartbeat for any received message
        self.__update_heartbeat()

    def on_receipt(self, *_):
        """
        Reset the last received time whenever a receipt is received.
        """
        self.__update_heartbeat()

    def on_error(self, *_):
        """
        Reset the last received time whenever an error is received.
        """
        self.__update_heartbeat()

    def on_heartbeat(self):
        """
        Reset the last received time whenever a heartbeat message is received.
        """
        self.__update_heartbeat()

    def on_send(self, frame):
        """
        Add the heartbeat header to the frame when connecting, and bump
        next outbound heartbeat timestamp.

        :param Frame frame: the Frame object
        """
        if frame.cmd in [CMD_CONNECT, CMD_STOMP] and self.heartbeats != (0, 0):
            frame.headers[HDR_HEARTBEAT] = "%s,%s" % self.heartbeats
        if self.next_outbound_heartbeat is not None:
            self.next_outbound_heartbeat = monotonic() + self.send_sleep

    def __update_heartbeat(self):
        # Honour any grace that has been already included
        if self.received_heartbeat is None:
            return
        now = monotonic()
        if now > self.received_heartbeat:
            self.received_heartbeat = now

    def __heartbeat_loop(self):
        """
        Main loop for sending (and monitoring received) heartbeats.
        """
        logging.debug("starting heartbeat loop")
        now = monotonic()

        # Setup the initial due time for the outbound heartbeat
        if self.send_sleep != 0:
            self.next_outbound_heartbeat = now + self.send_sleep
            logging.debug("calculated next outbound heartbeat as %s", self.next_outbound_heartbeat)

        while not self.heartbeat_terminate_event.is_set():
            now = monotonic()

            next_events = []
            if self.next_outbound_heartbeat is not None:
                next_events.append(self.next_outbound_heartbeat - now)
            if self.receive_sleep != 0:
                t = self.received_heartbeat + self.receive_sleep - now
                if t > 0:
                    next_events.append(t)
            sleep_time = min(next_events) if next_events else 0
            if sleep_time > 0:
                terminate = self.heartbeat_terminate_event.wait(sleep_time)
                if terminate:
                    break

            now = monotonic()

            if not self.transport.is_connected() or self.disconnecting:
                time.sleep(self.send_sleep)
                continue

            if self.send_sleep != 0 and now > self.next_outbound_heartbeat:
                logging.debug("sending a heartbeat message at %s", now)
                try:
                    self.transport.transmit(utils.Frame(None, {}, None))
                except exception.NotConnectedException:
                    logging.debug("lost connection, unable to send heartbeat")
                except Exception:
                    _, e, _ = sys.exc_info()
                    logging.debug("unable to send heartbeat, due to: %s", e)

            if self.receive_sleep != 0:
                diff_receive = now - self.received_heartbeat

                if diff_receive > self.receive_sleep:
                    # heartbeat timeout
                    logging.warning("heartbeat timeout: diff_receive=%s, time=%s, lastrec=%s",
                                    diff_receive, now, self.received_heartbeat)
                    self.transport.set_connected(False)
                    self.transport.disconnect_socket()
                    self.transport.stop()
                    for listener in self.transport.listeners.values():
                        listener.on_heartbeat_timeout()
        self.heartbeat_thread = None
        if self.heartbeats != (0, 0):
            # don't bother logging this if heartbeats weren't setup to start with
            logging.debug("heartbeat loop ended")


class WaitingListener(ConnectionListener):
    """
    A listener which waits for a specific receipt to arrive.
    """
    def __init__(self, receipt):
        """
        :param str receipt:
        """
        self.receipt_condition = threading.Condition()
        self.disconnect_condition = threading.Condition()
        self.receipt = receipt
        self.received = False
        self.disconnected = False

    def on_receipt(self, frame):
        """
        If the receipt id can be found in the headers, then notify the waiting thread.

        :param Frame frame: the stomp frame
        """
        if "receipt-id" in frame.headers and frame.headers["receipt-id"] == self.receipt:
            with self.receipt_condition:
                self.received = True
                self.receipt_condition.notify()

    def on_disconnected(self):
        with self.disconnect_condition:
            self.disconnected = True
            self.disconnect_condition.notify()

    def wait_on_receipt(self):
        """
        Wait until we receive a message receipt.
        """
        with self.receipt_condition:
            while not self.received:
                self.receipt_condition.wait()
            self.received = False

    def wait_on_disconnected(self):
        """
        Wait until disconnected.
        """
        with self.disconnect_condition:
            while not self.disconnected:
                self.disconnect_condition.wait()


class StatsListener(ConnectionListener):
    """
    A connection listener for recording statistics on messages sent and received.
    """
    def __init__(self):
        # The number of errors received
        self.errors = 0
        # The number of connections established
        self.connections = 0
        # The number of disconnections
        self.disconnects = 0
        # The number of messages received
        self.messages = 0
        # The number of messages sent
        self.messages_sent = 0
        # The number of heartbeat timeouts
        self.heartbeat_timeouts = 0
        # The number of heartbeats
        self.heartbeat_count = 0

    def on_disconnected(self):
        """
        Increment the disconnect count. See :py:meth:`ConnectionListener.on_disconnected`
        """
        self.disconnects += 1
        logging.info("disconnected (x %s)", self.disconnects)

    def on_error(self, frame):
        """
        Increment the error count. See :py:meth:`ConnectionListener.on_error`

        :param Frame frame: the stomp frame
        """
        if logging.isEnabledFor(logging.DEBUG):
            logging.debug("received an error %s [%s]", frame.body, frame.headers)
        else:
            logging.info("received an error %s", frame.body)
        self.errors += 1

    def on_connecting(self, host_and_port):
        """
        Increment the connection count. See :py:meth:`ConnectionListener.on_connecting`

        :param (str,int) host_and_port: the host and port as a tuple
        """
        logging.info("connecting %s %s (x %s)", host_and_port[0], host_and_port[1], self.connections)
        self.connections += 1

    def on_message(self, frame):
        """
        Increment the message received count. See :py:meth:`ConnectionListener.on_message`

        :param Frame frame: the stomp frame
        """
        self.messages += 1

    def on_send(self, frame):
        """
        Increment the send count. See :py:meth:`ConnectionListener.on_send`

        :param Frame frame:
        """
        self.messages_sent += 1

    def on_heartbeat_timeout(self):
        """
        Increment the heartbeat timeout. See :py:meth:`ConnectionListener.on_heartbeat_timeout`
        """
        logging.debug("received heartbeat timeout")
        self.heartbeat_timeouts += 1

    def on_heartbeat(self):
        """
        Increment the heartbeat count. See :py:meth:`ConnectionListener.on_heartbeat`
        """
        self.heartbeat_count += 1

    def __str__(self):
        """
        Return a string containing the current statistics (messages sent and received,
        errors, etc)
        """
        return '''Connections: %s
Disconnects: %s
Messages sent: %s
Messages received: %s
Heartbeats received: %s
Errors: %s''' % (self.connections, self.disconnects, self.messages_sent, self.messages,
                 self.heartbeat_count, self.errors)


class PrintingListener(ConnectionListener):
    def __init__(self, print_to_log=False):
        self.print_to_log = print_to_log

    def __print(self, msg, *args):
        if self.print_to_log:
            logging.info(msg, *args)
        else:
            print(msg % args)

    def on_connecting(self, host_and_port):
        """
        :param (str,int) host_and_port:
        """
        self.__print("on_connecting %s %s", *host_and_port)

    def on_connected(self, frame):
        """
        :param Frame frame: the stomp frame
        """
        self.__print("on_connected %s %s", frame.headers, frame.body)

    def on_disconnected(self):
        self.__print("on_disconnected")

    def on_heartbeat_timeout(self):
        self.__print("on_heartbeat_timeout")

    def on_before_message(self, frame):
        """
        :param Frame frame: the stomp frame
        """
        self.__print("on_before_message %s %s", frame.headers, frame.body)

    def on_message(self, frame):
        """
        :param Frame frame: the stomp frame
        """
        self.__print("on_message %s %s", frame.headers, frame.body)

    def on_receipt(self, frame):
        """
        :param Frame frame: the stomp frame
        """
        self.__print("on_receipt %s %s", frame.headers, frame.body)

    def on_error(self, frame):
        """
        :param Frame frame: the stomp frame
        """
        self.__print("on_error %s %s", frame.headers, frame.body)

    def on_send(self, frame):
        """
        :param Frame frame: the stomp frame
        """
        self.__print("on_send %s %s %s", frame.cmd, utils.clean_headers(frame.headers), frame.body)

    def on_heartbeat(self):
        self.__print("on_heartbeat")


class TestListener(StatsListener, WaitingListener, PrintingListener):
    """
    Implementation of StatsListener and WaitingListener. Useful for testing.
    """
    def __init__(self, receipt=None, print_to_log=False):
        """
        :param str receipt:
        """
        StatsListener.__init__(self)
        PrintingListener.__init__(self, print_to_log)
        WaitingListener.__init__(self, receipt)
        self.message_list = []
        self.message_condition = threading.Condition()
        self.message_received = False
        self.heartbeat_condition = threading.Condition()
        self.heartbeat_received = False
        self.timestamp = time.strftime("%Y%m%d%H%M%S")

    def wait_for_message(self):
        with self.message_condition:
            while not self.message_received:
                self.message_condition.wait()
            self.message_received = False

    def get_latest_message(self):
        return self.message_list[-1]

    def wait_for_heartbeat(self):
        with self.heartbeat_condition:
            while not self.heartbeat_received:
                self.heartbeat_condition.wait()
            self.heartbeat_received = False

    def on_connecting(self, host_and_port):
        StatsListener.on_connecting(self, host_and_port)
        PrintingListener.on_connecting(self, host_and_port)
        WaitingListener.on_connecting(self, host_and_port)

    def on_connected(self, frame):
        StatsListener.on_connected(self, frame)
        PrintingListener.on_connected(self, frame)
        WaitingListener.on_connected(self, frame)

    def on_disconnected(self):
        StatsListener.on_disconnected(self)
        PrintingListener.on_disconnected(self)
        WaitingListener.on_disconnected(self)

    def on_heartbeat_timeout(self):
        StatsListener.on_heartbeat_timeout(self)
        PrintingListener.on_heartbeat_timeout(self)
        WaitingListener.on_heartbeat_timeout(self)

    def on_before_message(self, frame):
        StatsListener.on_before_message(self, frame)
        PrintingListener.on_before_message(self, frame)
        WaitingListener.on_before_message(self, frame)

    def on_message(self, frame):
        """
        :param Frame frame: the stomp frame
        """
        StatsListener.on_message(self, frame)
        PrintingListener.on_message(self, frame)
        self.message_list.append((frame.headers, frame.body))
        with self.message_condition:
            self.message_received = True
            self.message_condition.notify()

    def on_receipt(self, frame):
        StatsListener.on_receipt(self, frame)
        PrintingListener.on_receipt(self, frame)
        WaitingListener.on_receipt(self, frame)

    def on_error(self, frame):
        StatsListener.on_error(self, frame)
        PrintingListener.on_error(self, frame)
        WaitingListener.on_error(self, frame)

    def on_send(self, frame):
        StatsListener.on_send(self, frame)
        PrintingListener.on_send(self, frame)
        WaitingListener.on_send(self, frame)

    def on_heartbeat(self):
        StatsListener.on_heartbeat(self)
        PrintingListener.on_heartbeat(self)
        with self.heartbeat_condition:
            self.heartbeat_received = True
            self.heartbeat_condition.notify()

    def on_receiver_loop_completed(self, frame):
        StatsListener.on_receiver_loop_completed(self, frame)
        PrintingListener.on_receiver_loop_completed(self, frame)
        WaitingListener.on_receiver_loop_completed(self, frame)
