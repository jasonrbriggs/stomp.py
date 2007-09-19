#!/usr/bin/env python

"""Stomp Protocol Connectivity

    This provides basic connectivity to a message broker supporting the 'stomp' protocol.
    At the moment ACK, SEND, SUBSCRIBE, UNSUBSCRIBE, BEGIN, ABORT, COMMIT and DISCONNECT operations
    are supported.  CONNECT is implicit.
    
    This changes the previous version which required a listener per subscription -- now a listener object
    just calls the 'addlistener' method and will receive all messages sent in response to all/any subscriptions.
    (The reason for the change is that the handling of an 'ack' becomes problematic unless the listener mechanism
    is decoupled from subscriptions).
    
    Note that you must 'start' an instance of Connection to begin receiving messages.  For example:
    
        conn = stomp.Connection('localhost', 62003, 'myuser', 'mypass')
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
      
    Updates
    -------
    * 2007/03/31 : (Andreas Schobel) patch to fix newlines problem in ActiveMQ 4.1
    * 2007/09    : (JRB) updated to get stomp.py working in Jython as well as Python
    * 2007/09/05 : (Julian Scheid) patch to allow sending custom headers
    * 2007/09/18 : (JRB) changed code to use logging instead of just print. added logger for jython to work
    * 2007/09/19 : (Julian Scheid) various updates, including:
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
"""

import md5
import random
import re
import socket
import sys
import thread
import time
import math

#
# stomp.py version number
#
_version = 1.5
 
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

    
class ConnectionClosedException(Exception):
    """
    Raised in the receiver thread when the connection has been closed
    by the server.
    """
    pass


class NotConnectedException(Exception):
    """
    Raised by Connection.__send when there is currently no server
    connection.
    """
    pass


class DevNullLogger(object):
    """
    dummy logging class for environments without the logging module
    """
    def devnull(self, msg):
        pass
    debug = devnull
    info = devnull
    warning = devnull
    error = devnull
    critical = devnull
        
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
        

class Connection(object):

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

            sorted_host_and_ports.sort(lambda x, y: int(is_local_host(y[0])) - int(is_local_host(x[0])))

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
        self.host_and_ports = []
        self.host_and_ports.extend(loopback_host_and_ports)
        self.host_and_ports.extend(sorted_host_and_ports)

        self.recvbuf = ''

        self.listeners = [ ]

        self.reconnect_sleep_initial = reconnect_sleep_initial
        self.reconnect_sleep_increase = reconnect_sleep_increase
        self.reconnect_sleep_jitter = reconnect_sleep_jitter
        self.reconnect_sleep_max = reconnect_sleep_max
        
        self.__connect_headers = {}
        if user is not None and passcode is not None:
            self.__connect_headers['login'] = user
            self.__connect_headers['passcode'] = passcode

        self.socket = None

    #
    # Manage the connection
    #

    def start(self):
        self.running = True
        thread.start_new_thread(self.__receiver_loop, ())

    def stop(self):
        self.disconnect()

    #
    # Manage objects listening to incoming frames
    #

    def addlistener(self, listener):
        self.listeners.append(listener)
        
    def dellistener(self, listener):
        self.listeners.remove(listener)

    #
    # STOMP transmissions
    #
        
    def subscribe(self, dest, ack='auto'):
        self.__send('SUBSCRIBE', { 'destination': dest, 'ack': ack })

    def unsubscribe(self, dest):
        self.__send('UNSUBSCRIBE', { 'destination': dest })
        
    def send(self, dest, msg, transactionid=None, custom_headers={}):
        headers = { 'destination': dest }
        headers.update(custom_headers)
        if transactionid:
            headers['transaction'] = transactionid
        self.__send('SEND', headers, msg)
    
    def ack(self, messageid, transactionid=None):
        headers = { 'message-id': messageid }
        if transactionid:
            headers['transaction'] = transactionid
        self.__send('ACK', headers)
        
    def begin(self, transactionid=None):
        if not transactionid:
            transactionid = _uuid()
        self.__send('BEGIN', { 'transaction': transactionid })
        return transactionid        

    def abort(self, transactionid):
        self.__send('ABORT', { 'transaction': transactionid })
        
    def commit(self, transactionid):
        self.__send('COMMIT', { 'transaction': transactionid })

    def sendblank(self):
        self.sendbuf.append('\x00\n')
        
    def disconnect(self):
        self.__send('DISCONNECT')
        self.running = False
        self.socket.close()


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
    

    def __receiver_loop(self):
        """
        Main loop listening for incoming data.
        """
        while self.running:
            self.__attempt_connection()

            if self.socket is None:
                return

            try:
                try:
                    self.__send('CONNECT', self.__connect_headers)

                    while self.running:
                        packets = self.__read()

                        for packet in packets:
                            (frame_type, headers, body) = self.__parse_message(packet)
                            log.debug("Received frame: result=%s, headers=%s, body=%s" % (frame_type, headers, body))
                            frame_type = frame_type.lower()
                            if frame_type in [ 'connected', 'message', 'receipt', 'error' ]:
                                for listener in self.listeners:
                                    eval('listener.on_%s(headers, body)' % frame_type)
                            else:
                                log.warn('Unknown response frame type: "%s" (message length was %d)' % (frame_type, len(msg)))
                finally:
                    try:
                        self.socket.close()
                    except:
                        pass # ignore errors when attempting to close socket
                    self.socket = None
            except ConnectionClosedException:
                log.error("Lost connection")
                # Clear out any half-received messages after losing connection
                self.recvbuf = ''
                continue

    def __read(self):
        """
        Read the next message from the socket.
        """
        while self.running:
            c = self.socket.recv(1024)
            if len(c) == 0:
                raise ConnectionClosedException
            self.recvbuf += c
            if '\x00' in c:
                break
        result = []
        if len(self.recvbuf) > 0 and self.running:
            while True:
                pos = self.recvbuf.find('\x00')
                if pos >= 0:
                    result.append(self.recvbuf[0:pos])
                    self.recvbuf = self.recvbuf[pos+1:]
                else:
                    break
        return result

    def __parse_message(self, msg):
        """
        Parse a STOMP message into a (frame_type, headers, body)
        tuple, where frame_type is the frame type as a string
        (e.g. MESSAGE), headers is a map containing all header
        key/value pairs, and body is a string containing the message
        payload.
        """
        preamble_end = msg.find('\n\n')
        preamble = msg[0:preamble_end]
        preamble_lines = preamble.split('\n')
        body = msg[preamble_end+2:]
        first_line = 0
        while first_line < len(preamble_lines) and len(preamble_lines[first_line]) == 0:
            first_line += 1
        frame_type = preamble_lines[first_line]
        headers = {}
        for header_line in preamble_lines[first_line+1:]:
            header_match = Connection.__header_line_re.match(header_line)
            if header_match:
                headers[header_match.group('key')] = header_match.group('value')
        return (frame_type, headers, body)

    def __attempt_connection(self):
        """
        Try connecting to the (host, port) tuples specified at
        construction time.
        """
        sleep_exp = 1
        while self.running and self.socket is None:
            for host_and_port in self.host_and_ports:
                try:
                    log.debug("Attempting connection to host %s, port %s" % host_and_port)
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.socket.connect(host_and_port)
                    log.info("Established connection to host %s, port %s" % host_and_port)
                    break
                except socket.error:
                    self.socket = None
                    log.warn("Could not connect to host %s, port %s: %s" % (host_and_port[0], host_and_port[1], sys.exc_info()[1][1]))

            if self.socket is None:
                sleep_duration = (min(self.reconnect_sleep_max, 
                                      ((self.reconnect_sleep_initial / (1.0 + self.reconnect_sleep_increase)) 
                                       * math.pow(1.0 + self.reconnect_sleep_increase, sleep_exp)))
                                  * (1.0 + random.random() * self.reconnect_sleep_jitter))
                sleep_end = time.time() + sleep_duration
                log.debug("Sleeping for %.1f seconds before attempting reconnect" % sleep_duration)
                while self.running and time.time() < sleep_end:
                    time.sleep(0.2)

                sleep_exp += 1
        
    def __send(self, command, headers={}, payload=''):
        """
        Send a STOMP packet.
        """
        if self.socket is not None:
            message = '%s\n%s\n%s\x00' % (command,
                                            reduce(lambda accu, key: accu + ('%s: %s\n' % (key, headers[key])), headers.keys(), ''),
                                            payload)        
            self.socket.sendall(message)
        else:
            raise NotConnectedException()
     

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
        def __init__(self, host, port, user='', passcode=''):
            self.c = Connection([(host, port)], user, passcode)
            self.c.addlistener(self)
            self.c.start()

        def __print_async(self, frame_type, headers, body):
            print "\r  \r"
            print frame_type
            for header_key in headers.keys():
                print '%s: %s' % (header_key, headers[header_key])
            print
            print body
            print '> ',
            sys.stdout.flush()

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
                self.c.ack(args[1])
            else:
                self.c.ack(args[1], args[2])
            
        def abort(self, args):
            self.c.abort(args[1])
            
        def begin(self, args):
            print 'transaction id: %s' % self.c.begin()
            
        def blank(self, args):
            self.c.sendblank()
            
        def commit(self, args):
            if len(args) < 2:
                print 'expecting: commit <transid>'
            else:
                print 'committing %s' % args[1]
                self.c.commit(args[1])
       
        def disconnect(self, args):
            try:
                self.c.disconnect()
            except NotConnectedException:
                pass # ignore if no longer connected
            
        def send(self, args):
            if len(args) < 3:
                print 'expecting: send <destination> <message>'
            else:
                self.c.send(args[1], ' '.join(args[2:]))
            
        def sendtrans(self, args):
            if len(args) < 3:
                print 'expecting: sendtrans <destination> <transid> <message>'
            else:
                self.c.send(args[1], "%s\n" % ' '.join(args[3:]), args[2])
            
        def subscribe(self, args):
            if len(args) < 2:
                print 'expecting: subscribe <destination> [ack]'
            elif len(args) > 2:
                print 'subscribing to "%s" with acknowledge set to "%s"' % (args[1], args[2])
                self.c.subscribe(args[1], args[2])
            else:
                print 'subscribing to "%s" with no acknowledge' % args[1]
                self.c.subscribe(args[1])
            
        def unsubscribe(self, args):
            if len(args) < 2:
                print 'expecting: unsubscribe <destination>'
            else:
                print 'unsubscribing from "%s"' % args[1]
                self.c.unsubscribe(args[1])

    try:
        if len(sys.argv) < 3:
            print 'USAGE: stomp.py host port [user] [passcode]'
            sys.exit(1)

        host = sys.argv[1]
        port = int(sys.argv[2])
        
        if len(sys.argv) >= 5:
            user = sys.argv[3]
            passcode = sys.argv[4]
        else:
            user = None
            passcode = None
        
        st = StompTester(host, port, user, passcode)
        while True:
            line = raw_input("\r> ")
            if not line or line.lstrip().rstrip() == '':
                continue
            elif 'quit' in line or 'disconnect' in line:
                st.disconnect(None)
                break
                
            split = line.split()
            command = split[0]
            if not command.startswith("on_") and hasattr(st, command):
                getattr(st, command)(split)
            else:
                print 'unrecognized command'
    except KeyboardInterrupt:
        st.disconnect(None)
