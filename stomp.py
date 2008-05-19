#!/usr/bin/env python

"""Stomp Protocol Connectivity

    This provides basic connectivity to a message broker supporting the 'stomp' protocol.
    At the moment ACK, SEND, SUBSCRIBE, UNSUBSCRIBE, BEGIN, ABORT, COMMIT, CONNECT and DISCONNECT operations
    are supported.
    
    This changes the previous version which required a listener per subscription -- now a listener object
    just calls the 'addlistener' method and will receive all messages sent in response to all/any subscriptions.
    (The reason for the change is that the handling of an 'ack' becomes problematic unless the listener mechanism
    is decoupled from subscriptions).
    
    Note that you must 'start' an instance of Connection to begin receiving messages.  For example:
    
        conn = stomp.Connection([('localhost', 62003)], 'myuser', 'mypass')
        conn.start()

    Meta-Data
    ---------
    Author: Jason R Briggs
    License: http://www.apache.org/licenses/LICENSE-2.0
    Start Date: 2005/12/01
    Last Revision Date: $Date: 2007/09/19 14:33 $
    
    Notes/Attribution
    -----------------
    * uuid method courtesy of Carl Free Jr:
      http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/213761
    * patch from Andreas Schobel
    * patches from Julian Scheid of Rising Sun Pictures (http://open.rsp.com.au)
    * patch from Fernando
      
    Updates
    -------
    * 2007/03/31 : (Andreas Schobel) patch to fix newlines problem in ActiveMQ 4.1
    * 2007/09    : (JRB) updated to get stomp.py working in Jython as well as Python
    * 2007/09/05 : (Julian Scheid) patch to allow sending custom headers
    * 2007/09/18 : (JRB) changed code to use logging instead of just print. added logger for jython to work
    * 2007/09/18 : (Julian Scheid) various updates, including:
       - change incoming message handling so that callbacks are invoked on the listener not only for MESSAGE, but also for 
            CONNECTED, RECEIPT and ERROR frames.
       - callbacks now get not only the payload but any headers specified by the server
       - all outgoing messages now sent via a single method
       - only one connection used 
       - change to use thread instead of threading
       - sends performed on the calling thread
       - receiver loop now deals with multiple messages in one received chunk of data
       - added reconnection attempts and connection fail-over
       - changed defaults for "user" and "passcode" to None instead of empty string (fixed transmission of those values)
       - added readline support
    * 2008/03/26 : (Fernando) added cStringIO for faster performance on large messages 
"""

import math
import md5
import random
import re
import socket
import sys
import thread
import threading
import time
import types
from cStringIO import StringIO

#
# stomp.py version number
#
_version = 1.6


def _uuid( *args ):
    """
    uuid courtesy of Carl Free Jr:
    (http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/213761)
    """
    
    t = long( time.time() * 1000 )
    r = long( random.random() * 100000000000000000L )
  
    try:
        a = socket.gethostbyname( socket.gethostname() )
    except:
        # if we can't get a network address, just imagine one
        a = random.random() * 100000000000000000L
    data = str(t) + ' ' + str(r) + ' ' + str(a) + ' ' + str(args)
    data = md5.md5(data).hexdigest()
  
    return data


class DevNullLogger(object):
    """
    dummy logging class for environments without the logging module
    """
    def log(self, msg):
        print msg
        
    def devnull(self, msg):
        pass
    
    debug = devnull
    info = devnull
    warning = log
    error = log
    critical = log
    exception = log
        
    def isEnabledFor(self, lvl):
        return False


#
# add logging if available
#
try:
    import logging
    log = logging.getLogger('stomp.py')
except ImportError:
    log = DevNullLogger()

    
class ConnectionClosedException(Exception):
    """
    Raised in the receiver thread when the connection has been closed
    by the server.
    """
    pass


class NotConnectedException(Exception):
    """
    Raised by Connection.__send_frame when there is currently no server
    connection.
    """
    pass


class ConnectionListener(object):
    """
    This class should be used as a base class for objects registered
    using Connection.add_listener().
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


class Connection(object):
    """
    Represents a STOMP client connection.
    """

    def __init__(self, 
                 host_and_ports = [ ('localhost', 61613) ], 
                 user = None,
                 passcode = None,
                 prefer_localhost = True,
                 try_loopback_connect = True,
                 reconnect_sleep_initial = 0.1,
                 reconnect_sleep_increase = 0.5,
                 reconnect_sleep_jitter = 0.1,
                 reconnect_sleep_max = 60.0):
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

        \param reonnect_sleep_max

                 maximum delay between connection attempts, regardless
                 of the reconnect_sleep_increase.

        \param reconnect_sleep_jitter

                 random additional time to wait (as a percentage of
                 the time determined using the previous parameters)
                 between connection attempts in order to avoid
                 stampeding. For example, a value of 0.1 means to wait
                 an extra 0%-10% (randomly determined) of the delay
                 calculated using the previous three parameters.
        """

        sorted_host_and_ports = []
        sorted_host_and_ports.extend(host_and_ports)

        # If localhost is preferred, make sure all (host, port) tuples
        # that refer to the local host come first in the list
        if prefer_localhost:
            def is_local_host(host):
                return host in Connection.__localhost_names

            sorted_host_and_ports.sort(lambda x, y: (int(is_local_host(y[0])) 
                                                     - int(is_local_host(x[0]))))

        # If the user wishes to attempt connecting to local ports
        # using the loopback interface, for each (host, port) tuple
        # referring to a local host, add an entry with the host name
        # replaced by 127.0.0.1 if it doesn't exist already
        loopback_host_and_ports = []
        if try_loopback_connect:
            for host_and_port in sorted_host_and_ports:
                if is_local_host(host_and_port[0]):
                    port = host_and_port[1]
                    if (not ("127.0.0.1", port) in sorted_host_and_ports 
                        and not ("localhost", port) in sorted_host_and_ports):
                        loopback_host_and_ports.append(("127.0.0.1", port))

        # Assemble the final, possibly sorted list of (host, port) tuples
        self.__host_and_ports = []
        self.__host_and_ports.extend(loopback_host_and_ports)
        self.__host_and_ports.extend(sorted_host_and_ports)

        self.__recvbuf = ''

        self.__listeners = [ ]

        self.__reconnect_sleep_initial = reconnect_sleep_initial
        self.__reconnect_sleep_increase = reconnect_sleep_increase
        self.__reconnect_sleep_jitter = reconnect_sleep_jitter
        self.__reconnect_sleep_max = reconnect_sleep_max
        
        self.__connect_headers = {}
        if user is not None and passcode is not None:
            self.__connect_headers['login'] = user
            self.__connect_headers['passcode'] = passcode

        self.__socket = None
        self.__current_host_and_port = None

        self.__receiver_thread_exit_condition = threading.Condition()
        self.__receiver_thread_exited = False

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
        thread.start_new_thread(self.__receiver_loop, ())
        self.__attempt_connection()

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
        
    #
    # Manage objects listening to incoming frames
    #

    def add_listener(self, listener):
        self.__listeners.append(listener)
        
    def remove_listener(self, listener):
        self.__listeners.remove(listener)

    #
    # STOMP transmissions
    #

    def subscribe(self, headers={}, **keyword_headers):
        self.__send_frame_helper('SUBSCRIBE', '', self.__merge_headers([headers, keyword_headers]), [ 'destination' ])

    def unsubscribe(self, headers={}, **keyword_headers):
        self.__send_frame_helper('UNSUBSCRIBE', '', self.__merge_headers([headers, keyword_headers]), [ ('destination', 'id') ])
        
    def send(self, message='', headers={}, **keyword_headers):
        if '\x00' in message:
            content_length_headers = {'content-length': len(message)}
        else:
            content_length_headers = {}
        self.__send_frame_helper('SEND', message, self.__merge_headers([headers, 
                                                                        keyword_headers,
                                                                        content_length_headers]), [ 'destination' ])
    
    def ack(self, headers={}, **keyword_headers):
        self.__send_frame_helper('ACK', '', self.__merge_headers([headers, keyword_headers]), [ 'message-id' ])
        
    def begin(self, headers={}, **keyword_headers):
        use_headers = self.__merge_headers([headers, keyword_headers])
        if not 'transaction' in use_headers.keys(): use_headers['transaction'] = _uuid()
        self.__send_frame_helper('BEGIN', '', use_headers, [ 'transaction' ])
        return use_headers['transaction']

    def abort(self, headers={}, **keyword_headers):
        self.__send_frame_helper('ABORT', '', self.__merge_headers([headers, keyword_headers]), [ 'transaction' ])
        
    def commit(self, headers={}, **keyword_headers):
        self.__send_frame_helper('COMMIT', '', self.__merge_headers([headers, keyword_headers]), [ 'transaction' ])

    def connect(self, headers={}, **keyword_headers):
        self.__send_frame_helper('CONNECT', '', self.__merge_headers([headers, keyword_headers]), [ ])
        
    def disconnect(self, headers={}, **keyword_headers):
        self.__send_frame_helper('DISCONNECT', '', self.__merge_headers([self.__connect_headers, headers, keyword_headers]), [ ])
        self.__running = False
        if hasattr(socket, 'SHUT_RDWR'):
            self.__socket.shutdown(socket.SHUT_RDWR)
        self.__socket.close()
        self.__current_host_and_port = None

    # ========= PRIVATE MEMBERS =========


    # List of all host names (unqualified, fully-qualified, and IP
    # addresses) that refer to the local host (both loopback interface
    # and external interfaces).  This is used for determining
    # preferred targets.
    __localhost_names = [ "localhost",
                          "127.0.0.1",
                          socket.gethostbyname(socket.gethostname()),
                          socket.gethostname(),
                          socket.getfqdn(socket.gethostname()) ]
    #
    # Used to parse STOMP header lines in the format "key:value",
    #
    __header_line_re = re.compile('(?P<key>[^:]+)[:](?P<value>.*)')    

    #
    # Used to parse the STOMP "content-length" header lines,
    #
    __content_length_re = re.compile('^content-length[:]\\s*(?P<value>[0-9]+)', re.MULTILINE)

    def __merge_headers(self, header_map_list):
        """
        Helper function for combining multiple header maps into one.

        Any underscores ('_') in header names (keys) will be replaced
        by dashes ('-'), and header names will be converted to
        all-lowercase.
        """
        headers = {}
        for header_map in header_map_list:
            for header_key in header_map.keys():
                headers[header_key.replace('_', '-').lower()] = header_map[header_key]
        return headers

    def __send_frame_helper(self, command, payload, headers, required_header_keys):
        """
        Helper function for sending a frame after verifying that a
        given set of headers are present.

        \param command the command to send

        \param payload the frame's payload

        \param headers a dictionary containing the frame's headers

        \param required_header_keys a sequence enumerating all
        required header keys. If an element in this sequence is itself
        a tuple, that tuple is taken as a list of alternatives, one of
        which must be present.

        \throws ArgumentError if one of the required header keys is
        not present in the header map.
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
        """
        if self.__socket is not None:
            frame = '%s\n%s\n%s\x00' % (command,
                                        reduce(lambda accu, key: accu + ('%s: %s\n' % (key, headers[key])), headers.keys(), ''),
                                        payload)        
            self.__socket.sendall(frame)
            log.debug("Sent frame: type=%s, headers=%r, body=%r" % (command, headers, payload))
        else:
            raise NotConnectedException()

    def __receiver_loop(self):
        """
        Main loop listening for incoming data.
        """
        try:
            try:
                threading.currentThread().setName("StompReceiver")
                while self.__running:
                    self.__attempt_connection()

                    if self.__socket is None:
                        break

                    try:
                        try:
                            for listener in self.__listeners:
                                if hasattr(listener, 'on_connecting'):
                                    listener.on_connecting(self.__current_host_and_port)

                            while self.__running:
                                frames = self.__read()

                                for frame in frames:
                                    (frame_type, headers, body) = self.__parse_frame(frame)
                                    log.debug("Received frame: result=%r, headers=%r, body=%r" % (frame_type, headers, body))
                                    frame_type = frame_type.lower()
                                    if frame_type in [ 'connected', 
                                                       'message', 
                                                       'receipt', 
                                                       'error' ]:
                                        for listener in self.__listeners:
                                            if hasattr(listener, 'on_%s' % frame_type):
                                                eval('listener.on_%s(headers, body)' % frame_type)
                                            else:
                                                log.debug('listener %s has no such method on_%s' % (listener, frame_type)) 
                                    else:
                                        log.warning('Unknown response frame type: "%s" (frame length was %d)' % (frame_type, len(frame)))
                        finally:
                            try:
                                self.__socket.close()
                            except:
                                pass # ignore errors when attempting to close socket
                            self.__socket = None
                            self.__current_host_and_port = None
                    except ConnectionClosedException:
                        if self.__running:
                            log.error("Lost connection")
                            # Notify listeners
                            for listener in self.__listeners:
                                if hasattr(listener, 'on_disconnected'):
                                    listener.on_disconnected()
                            # Clear out any half-received messages after losing connection
                            self.__recvbuf = ''
                            continue
                        else:
                            break
            except:
                log.exception("An unhandled exception was encountered in the stomp receiver loop")

        finally:
            self.__receiver_thread_exit_condition.acquire()
            self.__receiver_thread_exited = True
            self.__receiver_thread_exit_condition.notifyAll()
            self.__receiver_thread_exit_condition.release()

    def __read(self):
        """
        Read the next frame(s) from the socket.
        """
        fastbuf = StringIO()
        while self.__running:
            try:
                c = self.__socket.recv(1024)
            except:
                c = ''
            if len(c) == 0:
                raise ConnectionClosedException
            fastbuf.write(c)
            if '\x00' in c:
                break
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
                                # Frame contains NUL bytes, need to
                                # read more
                                if frame_size < len(self.__recvbuf):
                                    pos = frame_size
                                    frame = self.__recvbuf[0:pos]
                                else:
                                    # Haven't read enough data yet,
                                    # exit loop and wait for more to
                                    # arrive
                                    break
                    result.append(frame)
                    self.__recvbuf = self.__recvbuf[pos+1:]
                else:
                    break
        return result

    def __parse_frame(self, frame):
        """
        Parse a STOMP frame into a (frame_type, headers, body) tuple,
        where frame_type is the frame type as a string (e.g. MESSAGE),
        headers is a map containing all header key/value pairs, and
        body is a string containing the frame's payload.
        """
        preamble_end = frame.find('\n\n')
        preamble = frame[0:preamble_end]
        preamble_lines = preamble.split('\n')
        body = frame[preamble_end+2:]

        # Skip any leading newlines
        first_line = 0
        while first_line < len(preamble_lines) and len(preamble_lines[first_line]) == 0:
            first_line += 1

        # Extract frame type
        frame_type = preamble_lines[first_line]

        # Put headers into a key/value map
        headers = {}
        for header_line in preamble_lines[first_line+1:]:
            header_match = Connection.__header_line_re.match(header_line)
            if header_match:
                headers[header_match.group('key')] = header_match.group('value')

        return (frame_type, headers, body)

    def __attempt_connection(self):
        """
        Try connecting to the (host, port) tuples specified at construction time.
        """
        lock = thread.allocate_lock()
        lock.acquire(1)
        try:
            sleep_exp = 1
            while self.__running and self.__socket is None:
                for host_and_port in self.__host_and_ports:
                    try:
                        log.debug("Attempting connection to host %s, port %s" % host_and_port)
                        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.__socket.connect(host_and_port)
                        self.__current_host_and_port = host_and_port
                        log.info("Established connection to host %s, port %s" % host_and_port)
                        break
                    except socket.error:
                        self.__socket = None
                        if type(sys.exc_info()[1]) == types.TupleType:
                            exc = sys.exc_info()[1][1]
                        else:
                            exc = sys.exc_info()[1]
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
    
                    sleep_exp += 1
        finally:
            lock.release()           

#
# command line testing
#
if __name__ == '__main__':

    # If the readline module is available, make command input easier
    try:
        import readline
        def stomp_completer(text, state):
            commands = [ 'subscribe', 'unsubscribe', 
                         'send',  'ack', 
                         'begin', 'abort', 'commit', 
                         'connect', 'disconnect'
                       ]
            for command in commands[state:]:
                if command.startswith(text):
                    return "%s " % command
            return None

        readline.parse_and_bind("tab: complete")
        readline.set_completer(stomp_completer)
        readline.set_completer_delims("")
    except ImportError:
        pass # ignore unavailable readline module

    class StompTester(object):
        def __init__(self, host='localhost', port=61613, user='', passcode=''):
            self.c = Connection([(host, port)], user, passcode)
            self.c.add_listener(self)
            self.c.start()

        def __print_async(self, frame_type, headers, body):
            print "\r  \r",
            print frame_type
            for header_key in headers.keys():
                print '%s: %s' % (header_key, headers[header_key])
            print
            print body
            print '> ',
            sys.stdout.flush()

        def on_connecting(self, host_and_port):
            self.c.connect()

        def on_disconnected(self):
            print "lost connection"

        def on_message(self, headers, body):
            self.__print_async("MESSAGE", headers, body)

        def on_error(self, headers, body):
            self.__print_async("ERROR", headers, body)

        def on_receipt(self, headers, body):
            self.__print_async("RECEIPT", headers, body)

        def on_connected(self, headers, body):
            self.__print_async("CONNECTED", headers, body)
            
        def ack(self, args):
            if len(args) < 3:
                self.c.ack(message_id=args[1])
            else:
                self.c.ack(message_id=args[1], transaction=args[2])
            
        def abort(self, args):
            self.c.abort(transaction=args[1])
            
        def begin(self, args):
            print 'transaction id: %s' % self.c.begin()
            
        def commit(self, args):
            if len(args) < 2:
                print 'expecting: commit <transid>'
            else:
                print 'committing %s' % args[1]
                self.c.commit(transaction=args[1])
       
        def disconnect(self, args):
            try:
                self.c.disconnect()
            except NotConnectedException:
                pass # ignore if no longer connected
            
        def send(self, args):
            if len(args) < 3:
                print 'expecting: send <destination> <message>'
            else:
                self.c.send(destination=args[1], message=' '.join(args[2:]))
            
        def sendtrans(self, args):
            if len(args) < 3:
                print 'expecting: sendtrans <destination> <transid> <message>'
            else:
                self.c.send(destination=args[1], message="%s\n" % ' '.join(args[3:]), transaction=args[2])
            
        def subscribe(self, args):
            if len(args) < 2:
                print 'expecting: subscribe <destination> [ack]'
            elif len(args) > 2:
                print 'subscribing to "%s" with acknowledge set to "%s"' % (args[1], args[2])
                self.c.subscribe(destination=args[1], ack=args[2])
            else:
                print 'subscribing to "%s" with auto acknowledge' % args[1]
                self.c.subscribe(destination=args[1], ack='auto')
            
        def unsubscribe(self, args):
            if len(args) < 2:
                print 'expecting: unsubscribe <destination>'
            else:
                print 'unsubscribing from "%s"' % args[1]
                self.c.unsubscribe(destination=args[1])

    if len(sys.argv) > 5:
        print 'USAGE: stomp.py [host] [port] [user] [passcode]'
        sys.exit(1)

    if len(sys.argv) >= 2:
        host = sys.argv[1]
    else:
        host = "localhost"
    if len(sys.argv) >= 3:
        port = int(sys.argv[2])
    else:
        port = 61613
    
    if len(sys.argv) >= 5:
        user = sys.argv[3]
        passcode = sys.argv[4]
    else:
        user = None
        passcode = None
    
    st = StompTester(host, port, user, passcode)
    try:
        while True:
            line = raw_input("\r> ")
            if not line or line.lstrip().rstrip() == '':
                continue
            elif 'quit' in line or 'disconnect' in line:
                break
            split = line.split()
            command = split[0]
            if not command.startswith("on_") and hasattr(st, command):
                getattr(st, command)(split)
            else:
                print 'unrecognized command'
    finally:
        st.disconnect(None)


