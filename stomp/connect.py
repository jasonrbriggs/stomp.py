import math
import random
import re
import socket
import sys
import threading
import time
import types
import xml.dom.minidom

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

try:
    import ssl
    from ssl import SSLError
    DEFAULT_SSL_VERSION = ssl.PROTOCOL_SSLv3
except ImportError: # python version < 2.6 without the backported ssl module
    ssl = None
    class SSLError:
        pass
    DEFAULT_SSL_VERSION = None

try:
    from socket import SOL_SOCKET, SO_KEEPALIVE
    from socket import SOL_TCP, TCP_KEEPIDLE, TCP_KEEPINTVL, TCP_KEEPCNT
    LINUX_KEEPALIVE_AVAIL=True
except ImportError:
    LINUX_KEEPALIVE_AVAIL=False

import exception
import listener
import utils
from backward import decode, encode, hasbyte, pack, socksend, NULL

try:
    import uuid    
except ImportError:
    from backward import uuid

try:
    from fractions import gcd
except ImportError:
    from backward import gcd

import logging
log = logging.getLogger('stomp.py')

class Connection(object):
    """
    Represents a STOMP client connection.
    """

    # ========= PRIVATE MEMBERS =========

    # List of all host names (unqualified, fully-qualified, and IP
    # addresses) that refer to the local host (both loopback interface
    # and external interfaces).  This is used for determining
    # preferred targets.
    __localhost_names = [ "localhost", "127.0.0.1" ]
    
    try:
        __localhost_names.append(socket.gethostbyname(socket.gethostname()))
    except:
        pass
        
    try:
        __localhost_names.append(socket.gethostname())
    except:
        pass
        
    try:
        __localhost_names.append(socket.getfqdn(socket.gethostname()))
    except:
        pass
    
    #
    # Used to parse the STOMP "content-length" header lines,
    #
    __content_length_re = re.compile('^content-length[:]\\s*(?P<value>[0-9]+)', re.MULTILINE)

    def __init__(self, 
                 host_and_ports = [ ('localhost', 61613) ], 
                 user = None,
                 passcode = None,
                 prefer_localhost = True,
                 try_loopback_connect = True,
                 reconnect_sleep_initial = 0.1,
                 reconnect_sleep_increase = 0.5,
                 reconnect_sleep_jitter = 0.1,
                 reconnect_sleep_max = 60.0,
                 reconnect_attempts_max = 3,
                 use_ssl = False,
                 ssl_key_file = None,
                 ssl_cert_file = None,
                 ssl_ca_certs = None,
                 ssl_cert_validator = None,
                 wait_on_receipt = False,
                 ssl_version = DEFAULT_SSL_VERSION,
                 timeout = None,
                 version = 1.0,
                 strict = True,
                 heartbeats = (0, 0),
                 keepalive = None
                 ):
        """
        Initialize and start this connection.

        \param host_and_ports            
            a list of (host, port) tuples.

        \param prefer_localhost
            if True and the local host is mentioned in the (host,
            port) tuples, try to connect to this first

        \param try_loopback_connect    
            if True and the local host is found in the host
            tuples, try connecting to it using loopback interface
            (127.0.0.1)

        \param reconnect_sleep_initial 
            initial delay in seconds to wait before reattempting
            to establish a connection if connection to any of the
            hosts fails.

        \param reconnect_sleep_increase 
            factor by which the sleep delay is increased after
            each connection attempt. For example, 0.5 means
            to wait 50% longer than before the previous attempt,
            1.0 means wait twice as long, and 0.0 means keep
            the delay constant.

        \param reconnect_sleep_max
            maximum delay between connection attempts, regardless
            of the reconnect_sleep_increase.

        \param reconnect_sleep_jitter
            random additional time to wait (as a percentage of
            the time determined using the previous parameters)
            between connection attempts in order to avoid
            stampeding. For example, a value of 0.1 means to wait
            an extra 0%-10% (randomly determined) of the delay
            calculated using the previous three parameters.
                 
        \param reconnect_attempts_max
            maximum attempts to reconnect
                
        \param use_ssl
            connect using SSL to the socket.  This wraps the 
            socket in a SSL connection.  The constructor will 
            raise an exception if you ask for SSL, but it can't
            find the SSL module.

        \param ssl_cert_file
            the path to a X509 certificate 

        \param ssl_key_file
            the path to a X509 key file

        \param ssl_ca_certs
            the path to the a file containing CA certificates
            to validate the server against.  If this is not set,
            server side certificate validation is not done. 

        \param ssl_cert_validator
            function which performs extra validation on the client
            certificate, for example checking the returned
            certificate has a commonName attribute equal to the
            hostname (to avoid man in the middle attacks).
            The signature is:
                (OK, err_msg) = validation_function(cert, hostname)
            where OK is a boolean, and cert is a certificate structure
            as returned by ssl.SSLSocket.getpeercert()
            
        \param wait_on_receipt
            if a receipt is specified, then the send method should wait
            (block) for the server to respond with that receipt-id
            before continuing
            
        \param ssl_version
            SSL protocol to use for the connection. This should be
            one of the PROTOCOL_x constants provided by the ssl module.
            The default is ssl.PROTOCOL_SSLv3
            
        \param timeout
            the timeout value to use when connecting the stomp socket
            
        \param version
            STOMP protocol version (1.0 or 1.1)
            
        \param strict
            if true, use the strict version of the protocol. For STOMP 1.1, this means
            it will use the STOMP connect header, rather than CONNECT.
            
        \param heartbeats
            a tuple containing the heartbeat send and receive time in millis. (0,0)
            if no heartbeats 

        \param keepalive
            some operating systems support sending the occasional heart
            beat packets to detect when a connection fails.  This
            parameter can either be set set to a boolean to turn on the
            default keepalive options for your OS, or as a tuple of
            values, which also enables keepalive packets, but specifies
            options specific to your OS implementation
        """

        sorted_host_and_ports = []
        sorted_host_and_ports.extend(host_and_ports)

        #
        # If localhost is preferred, make sure all (host, port) tuples that refer to the local host come first in the list
        #
        if prefer_localhost:
            sorted_host_and_ports.sort(key = self.is_localhost)

        #
        # If the user wishes to attempt connecting to local ports using the loopback interface, for each (host, port) tuple
        # referring to a local host, add an entry with the host name replaced by 127.0.0.1 if it doesn't exist already
        #
        loopback_host_and_ports = []
        if try_loopback_connect:
            for host_and_port in sorted_host_and_ports:
                if self.is_localhost(host_and_port) == 1:
                    port = host_and_port[1]
                    if (not ("127.0.0.1", port) in sorted_host_and_ports 
                        and not ("localhost", port) in sorted_host_and_ports):
                        loopback_host_and_ports.append(("127.0.0.1", port))

        #
        # Assemble the final, possibly sorted list of (host, port) tuples
        #
        self.__host_and_ports = []
        self.__host_and_ports.extend(loopback_host_and_ports)
        self.__host_and_ports.extend(sorted_host_and_ports)

        self.__recvbuf = ''

        self.__listeners = {}

        self.__reconnect_sleep_initial = reconnect_sleep_initial
        self.__reconnect_sleep_increase = reconnect_sleep_increase
        self.__reconnect_sleep_jitter = reconnect_sleep_jitter
        self.__reconnect_sleep_max = reconnect_sleep_max
        self.__reconnect_attempts_max = reconnect_attempts_max
        self.__timeout = timeout
        
        self.__connect_headers = {}
        if user is not None and passcode is not None:
            self.__connect_headers['login'] = user
            self.__connect_headers['passcode'] = passcode

        self.__socket = None
        self.__socket_semaphore = threading.BoundedSemaphore(1)
        self.__current_host_and_port = None

        self.__receiver_thread_exit_condition = threading.Condition()
        self.__receiver_thread_exited = False
        self.__send_wait_condition = threading.Condition()
        self.__connect_wait_condition = threading.Condition()
        
        self.blocking = None
        self.connected = False
        
        # setup SSL
        if use_ssl and not ssl:
            raise Exception("SSL connection requested, but SSL library not found.")
        self.__ssl = use_ssl
        self.__ssl_cert_file = ssl_cert_file
        self.__ssl_key_file = ssl_key_file
        self.__ssl_ca_certs = ssl_ca_certs
        self.__ssl_cert_validator = ssl_cert_validator
        self.__ssl_version = ssl_version
        
        self.__receipts = {}
        self.__wait_on_receipt = wait_on_receipt
        
        # protocol version
        self.version = version
        self.__strict = strict

        # setup heartbeating
        if version < 1.1 and heartbeats != (0, 0):
            raise exception.ProtocolException('Heartbeats can only be set on a 1.1+ connection')            
        self.heartbeats = heartbeats
        
        # used for 1.1 heartbeat messages (set to true every time a heartbeat message arrives)
        self.__received_heartbeat = time.time()
        
        # flag used when we receive the disconnect receipt
        self.__disconnect_receipt = None
        
        # function for creating threads used by the connection
        self.create_thread_fc = default_create_thread

        self.__keepalive = keepalive

    def is_localhost(self, host_and_port):
        """
        Return true if the specified host+port is a member of the 'localhost' list of hosts
        """
        (host, port) = host_and_port
        if host in Connection.__localhost_names:
            return 1
        else:
            return 2
            
    def override_threading(create_thread_fc):
        """
        Override for thread creation. Use an alternate threading library by
        setting this to a function with a single argument (which is the receiver loop callback).
        The thread which is returned should be started (ready to run)
        """
        self.create_thread_fc = create_thread_fc

    #
    # Manage the connection
    #

    def start(self):
        """
        Start the connection. This should be called after all
        listeners have been registered. If this method is not called,
        no frames will be received by the connection.
        """
        self.__running = True
        self.__attempt_connection()
        thread = self.create_thread_fc(self.__receiver_loop)
        self.__notify('connecting')

    def stop(self):
        """
        Stop the connection. This is equivalent to calling
        disconnect() but will do a clean shutdown by waiting for the
        receiver thread to exit.
        """
        self.disconnect()

        self.__receiver_thread_exit_condition.acquire()
        if not self.__receiver_thread_exited:
            self.__receiver_thread_exit_condition.wait()
        self.__receiver_thread_exit_condition.release()

    def get_host_and_port(self):
        """
        Return a (host, port) tuple indicating which STOMP host and
        port is currently connected, or None if there is currently no
        connection.
        """
        return self.__current_host_and_port
        
    def is_connected(self):
        """
        Return true if the socket managed by this connection is connected
        """
        try:
            return self.__socket is not None and self.__socket.getsockname()[1] != 0 and self.connected
        except socket.error:
            return False
        
    #
    # Manage objects listening to incoming frames
    #

    def set_listener(self, name, listener):
        """
        Set a named listener on this connection
        
        \see listener::ConnectionListener
        
        \param name the name of the listener
        \param listener the listener object
        """
        self.__listeners[name] = listener
        
    def remove_listener(self, name):
        """
        Remove a listener according to the specified name
        
        \param name the name of the listener to remove
        """
        del self.__listeners[name]

    def get_listener(self, name):
        """
        Return a named listener
        
        \param name the listener to return
        """
        if name in self.__listeners:
            return self.__listeners[name]
        else:
            return None

    #
    # STOMP transmissions
    #

    def subscribe(self, headers={}, **keyword_headers):
        """
        Send a SUBSCRIBE frame to subscribe to a queue
        """
        merged_headers = utils.merge_headers([headers, keyword_headers])
        required_headers = [ 'destination' ]
        if self.version >= 1.1:
            required_headers.append('id')
        self.__send_frame_helper('SUBSCRIBE', '', merged_headers, required_headers)

    def unsubscribe(self, headers={}, **keyword_headers):
        """
        Send an UNSUBSCRIBE frame to unsubscribe from a queue
        """
        merged_headers = utils.merge_headers([headers, keyword_headers])
        self.__send_frame_helper('UNSUBSCRIBE', '', merged_headers, [ ('destination', 'id') ])
        
    def send(self, message='', headers={}, **keyword_headers):
        """
        Send a message (SEND) frame
        """
        merged_headers = utils.merge_headers([headers, keyword_headers])
        
        if self.__wait_on_receipt and 'receipt' in merged_headers.keys():
            self.__send_wait_condition.acquire()
         
        self.__send_frame_helper('SEND', message, merged_headers, [ 'destination' ])
        self.__notify('send', headers, message)
        
        # if we need to wait-on-receipt, then block until the receipt frame arrives 
        if self.__wait_on_receipt and 'receipt' in merged_headers.keys():
            receipt = merged_headers['receipt']
            while receipt not in self.__receipts:
                self.__send_wait_condition.wait()
            self.__send_wait_condition.release()
            del self.__receipts[receipt]
    
    def ack(self, headers={}, **keyword_headers):
        """
        Send an ACK frame, to acknowledge receipt of a message
        """
        self.__send_frame_helper('ACK', '', utils.merge_headers([headers, keyword_headers]), [ 'message-id' ])
        
    def nack(self, headers={}, **keyword_headers):
        """
        Send an NACK frame, to acknowledge a message was not successfully processed
        """
        if self.version < 1.1:
            raise RuntimeError('NACK is not supported with 1.0 connections')
        self.__send_frame_helper('NACK', '', utils.merge_headers([headers, keyword_headers]), [ 'message-id' ])
        
    def begin(self, headers={}, **keyword_headers):
        """
        Send a BEGIN frame to start a transaction
        """
        use_headers = utils.merge_headers([headers, keyword_headers])
        if not 'transaction' in use_headers.keys(): 
            use_headers['transaction'] = str(uuid.uuid4())
        self.__send_frame_helper('BEGIN', '', use_headers, [ 'transaction' ])
        return use_headers['transaction']

    def abort(self, headers={}, **keyword_headers):
        """
        Send an ABORT frame to rollback a transaction
        """
        self.__send_frame_helper('ABORT', '', utils.merge_headers([headers, keyword_headers]), [ 'transaction' ])
        
    def commit(self, headers={}, **keyword_headers):
        """
        Send a COMMIT frame to commit a transaction (send pending messages)
        """
        self.__send_frame_helper('COMMIT', '', utils.merge_headers([headers, keyword_headers]), [ 'transaction' ])

    def connect(self, headers={}, **keyword_headers):
        """
        Send a CONNECT frame to start a connection
        """
        wait = False
        if 'wait' in keyword_headers and keyword_headers['wait']:
            wait = True
            del keyword_headers['wait']
            
        if self.version >= 1.1:
            if self.__strict:
                cmd = 'STOMP'
            else:
                cmd = 'CONNECT'
            headers['accept-version'] = self.version
            headers['heart-beat'] = '%s,%s' % self.heartbeats
        else:
            cmd = 'CONNECT'
        self.__send_frame_helper(cmd, '', utils.merge_headers([self.__connect_headers, headers, keyword_headers]), [ ])
        if wait:
            self.__connect_wait_condition.acquire()
            while not self.is_connected(): 
                self.__connect_wait_condition.wait()
            self.__connect_wait_condition.release()
        
    def disconnect_socket(self):
        self.__running = False
        if self.__socket is not None:
            if self.__ssl:
                #
                # Even though we don't want to use the socket, unwrap is the only API method which does a proper SSL shutdown
                #
                try:
                    self.__socket = self.__socket.unwrap()
                except Exception:
                    #
                    # unwrap seems flaky on Win with the backported ssl mod, so catch any exception and log it
                    #
                    _, e, _ = sys.exc_info()
                    log.warn(e)
            elif hasattr(socket, 'SHUT_RDWR'):
                try:
                    self.__socket.shutdown(socket.SHUT_RDWR)
                except socket.error:
                    _, e, _ = sys.exc_info()
                    log.warn('Unable to issue SHUT_RDWR on socket because of error "%s"' % e)

        #
        # split this into a separate check, because sometimes the socket is nulled between shutdown and this call
        #
        if self.__socket is not None:
            try:
                self.__socket.close()
            except socket.error:
                _, e, _ = sys.exc_info()
                log.warn('Unable to close socket because of error "%s"' % e)
        self.__current_host_and_port = None
        
    def disconnect(self, send_disconnect=True, headers={}, **keyword_headers):
        """
        Send a DISCONNECT frame to finish a connection
        """
        try:
            self.__send_frame_helper('DISCONNECT', '', utils.merge_headers([self.__connect_headers, headers, keyword_headers]), [ ])
        except exception.NotConnectedException:
            _, e, _ = sys.exc_info()
            self.disconnect_socket()
            raise e
        if self.version >= 1.1 and 'receipt' in headers:
            self.__disconnect_receipt = headers['receipt']
        else:
            self.disconnect_socket()

    def __convert_dict(self, payload):
        """
        Encode a python dictionary as a <map>...</map> structure.
        """
        xmlStr = "<map>\n"
        for key in payload:
            xmlStr += "<entry>\n"
            xmlStr += "<string>%s</string>" % key
            xmlStr += "<string>%s</string>" % payload[key]
            xmlStr += "</entry>\n"
        xmlStr += "</map>"
        return xmlStr

    def __send_frame_helper(self, command, payload, headers, required_header_keys):
        """
        Helper function for sending a frame after verifying that a
        given set of headers are present.

        \param command
            the command to send

        \param payload
            the frame's payload

        \param headers
            a dictionary containing the frame's headers

        \param required_header_keys
            a sequence enumerating all required header keys. If an element in this sequence is itself
            a tuple, that tuple is taken as a list of alternatives, one of which must be present.

        \throws ArgumentError
            if one of the required header keys is not present in the header map.
        """
        for required_header_key in required_header_keys:
            if type(required_header_key) == tuple:
                found_alternative = False
                for alternative in required_header_key:
                    if alternative in headers.keys():
                        found_alternative = True
                if not found_alternative:
                    raise KeyError("Command %s requires one of the following headers: %s" % (command, str(required_header_key)))
            elif not required_header_key in headers.keys():
                raise KeyError("Command %s requires header %r" % (command, required_header_key))
        self.__send_frame(command, headers, payload)

    def __send_frame(self, command, headers={}, payload=''):
        """
        Send a STOMP frame.
        
        \param command
            the frame command
        
        \param headers
            a map of headers (key-val pairs)
        
        \param payload
            the message payload
        """
        if type(payload) == dict:
            headers["transformation"] = "jms-map-xml"
            payload = self.__convert_dict(payload)  

        if payload:
            payload = encode(payload)

            if hasbyte(0, payload):
                headers.update({'content-length': len(payload)})
            
        if self.__socket is not None:
            try:
                frame = [ ]                
                if command is not None:
                    frame.append(command + '\n')
                    
                for key, val in headers.items():
                    frame.append('%s:%s\n' % (key, val))
                        
                frame.append('\n')
                    
                if payload:
                    frame.append(payload)
                    
                if command is not None:
                    # only send the terminator if we're sending a command (heartbeats have no term)
                    frame.append(NULL)
                frame = pack(frame)
                self.__socket_semaphore.acquire()
                try:
                    socksend(self.__socket, frame)
                    log.debug("Sent frame: type=%s, headers=%r, body=%r" % (command, headers, payload))
                finally:
                    self.__socket_semaphore.release()
            except Exception:
                _, e, _ = sys.exc_info()
                log.error("Error sending frame: %s" % e)
                raise e
        else:
            raise exception.NotConnectedException()

    def __notify(self, frame_type, headers=None, body=None):
        """
        Utility function for notifying listeners of incoming and outgoing messages
        
        \param frame_type
            the type of message
        
        \param headers
            the map of headers associated with the message
        
        \param body
            the content of the message
        """
        if frame_type == 'receipt':
            # logic for wait-on-receipt notification
            self.__send_wait_condition.acquire()
            self.__send_wait_condition.notify()
            self.__send_wait_condition.release()
            
            receipt = headers['receipt-id']
            self.__receipts[receipt] = None

            # received a stomp 1.1 disconnect receipt
            if receipt == self.__disconnect_receipt:
                self.disconnect_socket()

        if frame_type == 'connected':
            self.connected = True
            self.__connect_wait_condition.acquire()
            self.__connect_wait_condition.notify()
            self.__connect_wait_condition.release()
            if 'version' not in headers.keys():
                if self.version >= 1.1:
                    log.warn('Downgraded STOMP protocol version to 1.0')
                self.version = 1.0
            if 'heart-beat' in headers.keys():
                self.heartbeats = utils.calculate_heartbeats(headers['heart-beat'].replace(' ', '').split(','), self.heartbeats)
                if self.heartbeats != (0,0):
                    default_create_thread(self.__heartbeat_loop)

        for listener in self.__listeners.values():
            if not listener: continue
            if not hasattr(listener, 'on_%s' % frame_type):
                log.debug('listener %s has no method on_%s' % (listener, frame_type))
                continue

            if frame_type == 'connecting':
                listener.on_connecting(self.__current_host_and_port)
                continue
            elif frame_type == 'disconnected':
                self.connected = False
                listener.on_disconnected()
                continue

            notify_func = getattr(listener, 'on_%s' % frame_type)
            notify_func(headers, body)

    def __receiver_loop(self):
        """
        Main loop listening for incoming data.
        """
        log.debug("Starting receiver loop")
        try:
            try:
                while self.__running:
                    if self.__socket is None:
                        break

                    try:
                        try:
                            while self.__running:
                                frames = self.__read()
                                
                                for frame in frames:
                                    (frame_type, headers, body) = utils.parse_frame(frame)
                                    log.debug("Received frame: %r, headers=%r, body=%r" % (frame_type, headers, body))
                                    frame_type = frame_type.lower()
                                    if frame_type in [ 'connected', 'message', 'receipt', 'error' ]:
                                        self.__notify(frame_type, headers, body)
                                    elif frame_type == 'heartbeat':
                                        # no notifications needed
                                        pass
                                    else:
                                        log.warning('Unknown response frame type: "%s" (frame length was %d)' % (frame_type, len(frame)))
                        finally:
                            try:
                                self.__socket.close()
                            except:
                                pass # ignore errors when attempting to close socket
                            self.__socket = None
                            self.__current_host_and_port = None
                    except exception.ConnectionClosedException:
                        if self.__running:
                            log.error("Lost connection")
                            self.__notify('disconnected')
                            #
                            # Clear out any half-received messages after losing connection
                            #
                            self.__recvbuf = ''
                            self.__running = False
                        break
            except:
                log.exception("An unhandled exception was encountered in the stomp receiver loop")

        finally:
            self.__receiver_thread_exit_condition.acquire()
            self.__receiver_thread_exited = True
            self.__receiver_thread_exit_condition.notifyAll()
            self.__receiver_thread_exit_condition.release()
            log.debug("Receiver loop ended")
            
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
            sleep_time = gcd(send_sleep, receive_sleep) / 2
            
        send_time = time.time()
        receive_time = time.time()
            
        while self.__running:
            time.sleep(sleep_time)
            
            if time.time() - send_time > send_sleep:
                send_time = time.time()
                log.debug('Sending a heartbeat message')
                self.__send_frame(None)
            
            if time.time() - receive_time > receive_sleep:
                if time.time() - self.__received_heartbeat > receive_sleep:
                    log.debug('Heartbeat timeout')
                    # heartbeat timeout
                    for listener in self.__listeners.values():
                        listener.on_heartbeat_timeout()
                    self.disconnect_socket()
                    self.connected = False

    def __read(self):
        """
        Read the next frame(s) from the socket.
        """
        fastbuf = StringIO()
        while self.__running:
            try:
                c = self.__socket.recv(1024)
                c = decode(c)
                
                # reset the heartbeat for any received message
                self.__received_heartbeat = time.time()
            except Exception:
                _, e, _ = sys.exc_info()
                c = ''
            if len(c) == 0:
                raise exception.ConnectionClosedException()
            fastbuf.write(c)
            if '\x00' in c:
                break
            elif c == '\x0a':
                # heartbeat (special case)
                return c
        self.__recvbuf += fastbuf.getvalue()
        fastbuf.close() 
        result = []
        
        if len(self.__recvbuf) > 0 and self.__running:
            while True:
                pos = self.__recvbuf.find('\x00')

                if pos >= 0:
                    frame = self.__recvbuf[0:pos]
                    preamble_end = frame.find('\n\n')
                    if preamble_end >= 0:
                        content_length_match = Connection.__content_length_re.search(frame[0:preamble_end])
                        if content_length_match:
                            content_length = int(content_length_match.group('value'))
                            content_offset = preamble_end + 2
                            frame_size = content_offset + content_length
                            if frame_size > len(frame):
                                #
                                # Frame contains NUL bytes, need to read more
                                #
                                if frame_size < len(self.__recvbuf):
                                    pos = frame_size
                                    frame = self.__recvbuf[0:pos]
                                else:
                                    #
                                    # Haven't read enough data yet, exit loop and wait for more to arrive
                                    #
                                    break
                    result.append(frame)
                    self.__recvbuf = self.__recvbuf[pos+1:]
                else:
                    break
        return result

    def __enable_keepalive(self):
        def try_setsockopt(sock, name, fam, opt, val):
            if val is None:
                return True # no value to set always works
            try:
                sock.setsockopt(fam, opt, val)
                log.debug('keepalive: set %r option to %r on socket' % (name, val))
            except:
                log.error('keepalive: unable to set %r option to %r on socket' % (name,val))
                return False
            return True

        ka = self.__keepalive

        if not ka:
            return

        if ka == True:
            ka_sig = 'auto'
            ka_args = ()
        else:
            try:
                ka_sig = ka[0]
                ka_args = ka[1:]
            except Exception:
                log.error('keepalive: bad specification %r' % (ka,))
                return

        if ka_sig == 'auto':
            if LINUX_KEEPALIVE_AVAIL:
                ka_sig = 'linux'
                ka_args = None
                log.debug('keepalive: autodetected linux-style support')
            else:
                log.error('keepalive: unable to detect any implementation, DISABLED!')
                return

        if ka_sig == 'linux':
            log.debug('keepalive: activating linux-style support')
            if ka_args is None:
                log.debug('keepalive: using system defaults')
                ka_args = (None, None, None)
            lka_idle, lka_intvl, lka_cnt = ka_args
            if try_setsockopt(self.__socket, 'enable', SOL_SOCKET, SO_KEEPALIVE, 1):
                try_setsockopt(self.__socket, 'idle time', SOL_TCP, TCP_KEEPIDLE, lka_idle)
                try_setsockopt(self.__socket, 'interval', SOL_TCP, TCP_KEEPINTVL, lka_intvl)
                try_setsockopt(self.__socket, 'count', SOL_TCP, TCP_KEEPCNT, lka_cnt)
        else:
            log.error('keepalive: implementation %r not recognized or not supported' % ka_sig)

    def __attempt_connection(self):
        """
        Try connecting to the (host, port) tuples specified at construction time.
        """
        sleep_exp = 1
        connect_count = 0
        while self.__running and self.__socket is None and connect_count < self.__reconnect_attempts_max:
            for host_and_port in self.__host_and_ports:
                try:
                    log.debug("Attempting connection to host %s, port %s" % host_and_port)
                    self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.__enable_keepalive()

                    if self.__ssl: # wrap socket
                        if self.__ssl_ca_certs:
                            cert_validation = ssl.CERT_REQUIRED
                        else:
                            cert_validation = ssl.CERT_NONE
                        self.__socket = ssl.wrap_socket(self.__socket, keyfile = self.__ssl_key_file,
                                certfile = self.__ssl_cert_file, cert_reqs = cert_validation, 
                                ca_certs = self.__ssl_ca_certs, ssl_version = self.__ssl_version)
                    self.__socket.settimeout(self.__timeout)
                    if self.blocking is not None:
                        self.__socket.setblocking(self.blocking)
                    self.__socket.connect(host_and_port)
                    
                    #
                    # Validate server cert
                    #
                    if self.__ssl and self.__ssl_cert_validator: 
                        cert = self.__socket.getpeercert()
                        (ok, errmsg) = apply(self.__ssl_cert_validator, (cert, host_and_port[0]))
                        if not ok:
                            raise SSLError("Server certificate validation failed: %s" % errmsg)

                    self.__current_host_and_port = host_and_port
                    log.info("Established connection to host %s, port %s" % host_and_port)
                    break
                except socket.error:
                    self.__socket = None
                    if isinstance(sys.exc_info()[1], tuple):
                        exc = sys.exc_info()[1][1]
                    else:
                        exc = sys.exc_info()[1]
                    connect_count += 1
                    log.warning("Could not connect to host %s, port %s: %s" % (host_and_port[0], host_and_port[1], exc))

            if self.__socket is None:
                sleep_duration = (min(self.__reconnect_sleep_max, 
                                      ((self.__reconnect_sleep_initial / (1.0 + self.__reconnect_sleep_increase)) 
                                       * math.pow(1.0 + self.__reconnect_sleep_increase, sleep_exp)))
                                  * (1.0 + random.random() * self.__reconnect_sleep_jitter))
                sleep_end = time.time() + sleep_duration
                log.debug("Sleeping for %.1f seconds before attempting reconnect" % sleep_duration)
                while self.__running and time.time() < sleep_end:
                    time.sleep(0.2)

                if sleep_duration < self.__reconnect_sleep_max:
                    sleep_exp += 1

        if not self.__socket:
            raise exception.ConnectFailedException()


def default_create_thread(callback):
    """
    Default thread creation
    """
    thread = threading.Thread(None, callback)
    thread.daemon = True  # Don't let receiver thread prevent termination
    thread.start()
    return thread
