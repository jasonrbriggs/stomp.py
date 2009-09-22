#!/usr/bin/env python

import math
import random
import re
import socket
import sys
import thread
import threading
import time
import types
import xml.dom.minidom
from cStringIO import StringIO

try:
    import ssl
    from ssl import SSLError
except ImportError: # python version < 2.6 without the backported ssl module
    ssl = None
    class SSLError:
        pass
    
from exception import *
from listener import *
from utils import *

import logging
import logging.config
try:
    logging.config.fileConfig('stomp.log.conf')
except:
    pass      
log = logging.getLogger('stomp.py')
if not log:
    log = DevNullLogger()


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
    # Used to parse STOMP header lines in the format "key:value",
    #
    __header_line_re = re.compile('(?P<key>[^:]+)[:](?P<value>.*)')

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
                 use_ssl = False,
                 ssl_key_file = None,
                 ssl_cert_file = None,
                 ssl_ca_certs = None,
                 ssl_cert_validator = None):
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

        \param use_ssl

                 connect using SSL to the socket.  This wraps the 
                 socket in a SSL connection.  The constructor will 
                 raise an exception if you ask for SSL, but it can't
                 find the SSL module.

        \param ssl_cert_file

                 The path to a X509 certificate 

        \param ssl_key_file

                 The path to a X509 key file

        \param ssl_ca_certs

                 The path to the a file containing CA certificates
                 to validate the server against.  If this is not set,
                 server side certificate validation is not done. 

        \param ssl_cert_validator

                 Function which performs extra validation on the client
                 certificate, for example checking the returned
                 certificate has a commonName attribute equal to the
                 hostname (to avoid man in the middle attacks)

                 The signature is:
                     (OK, err_msg) = validation_function(cert, hostname)

                 where OK is a boolean, and cert is a certificate structure
                 as returned by ssl.SSLSocket.getpeercert()

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

        self.__listeners = {}

        self.__reconnect_sleep_initial = reconnect_sleep_initial
        self.__reconnect_sleep_increase = reconnect_sleep_increase
        self.__reconnect_sleep_jitter = reconnect_sleep_jitter
        self.__reconnect_sleep_max = reconnect_sleep_max
        
        self.__connect_headers = {}
        if user is not None and passcode is not None:
            self.__connect_headers['login'] = user
            self.__connect_headers['passcode'] = passcode

        self.__socket = None
        self.__socket_semaphore = threading.BoundedSemaphore(1)
        self.__current_host_and_port = None

        self.__receiver_thread_exit_condition = threading.Condition()
        self.__receiver_thread_exited = False

        if use_ssl and not ssl:
            print "Raising exception ..."
            raise Exception("SSL connection requested, but SSL library not found.")
        self.__ssl = use_ssl
        self.__ssl_cert_file = ssl_cert_file
        self.__ssl_key_file = ssl_key_file
        self.__ssl_ca_certs = ssl_ca_certs
        self.__ssl_cert_validator = ssl_cert_validator

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
        thread.start_new_thread(self.__receiver_loop, ())

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
        try:
            return self.__socket is not None and self.__socket.getsockname()[1] != 0
        except socket.error:
            return False
        
    #
    # Manage objects listening to incoming frames
    #

    def set_listener(self, name, listener):
        self.__listeners[name] = listener
        
    def remove_listener(self, name):
        del self.__listeners[name]

    def get_listener(self, name):
        if self.__listeners.has_key(name):
            return self.__listeners[name]
        else:
            return None

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
        self.__notify('send', headers, message)
    
    def ack(self, headers={}, **keyword_headers):
        self.__send_frame_helper('ACK', '', self.__merge_headers([headers, keyword_headers]), [ 'message-id' ])
        
    def begin(self, headers={}, **keyword_headers):
        use_headers = self.__merge_headers([headers, keyword_headers])
        if not 'transaction' in use_headers.keys(): 
            use_headers['transaction'] = _uuid()
        self.__send_frame_helper('BEGIN', '', use_headers, [ 'transaction' ])
        return use_headers['transaction']

    def abort(self, headers={}, **keyword_headers):
        self.__send_frame_helper('ABORT', '', self.__merge_headers([headers, keyword_headers]), [ 'transaction' ])
        
    def commit(self, headers={}, **keyword_headers):
        self.__send_frame_helper('COMMIT', '', self.__merge_headers([headers, keyword_headers]), [ 'transaction' ])

    def connect(self, headers={}, **keyword_headers):
        if keyword_headers.has_key('wait') and keyword_headers['wait']:
            while not self.is_connected(): time.sleep(0.1)
            del keyword_headers['wait']
        self.__send_frame_helper('CONNECT', '', self.__merge_headers([self.__connect_headers, headers, keyword_headers]), [ ])
        
    def disconnect(self, headers={}, **keyword_headers):
        self.__send_frame_helper('DISCONNECT', '', self.__merge_headers([self.__connect_headers, headers, keyword_headers]), [ ])
        self.__running = False
        
        if self.__socket is not None:
            if self.__ssl:
                # Even though we don't want to use the socket, unwrap is the only API method which does a proper SSL shutdown
                self.__socket = self.__socket.unwrap()
            elif hasattr(socket, 'SHUT_RDWR'):
                    self.__socket.shutdown(socket.SHUT_RDWR)
            if self.__socket is not None:
                self.__socket.close()
        self.__current_host_and_port = None

    def __merge_headers(self, header_map_list):
        """
        Helper function for combining multiple header maps into one.
        """
        headers = {}
        for header_map in header_map_list:
            for header_key in header_map.keys():
                headers[header_key] = header_map[header_key]
        return headers
        
    def __convert_dict(self, payload):
        """
        Encode python dictionary as <map>...</map> structure.
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
        if type(payload) == dict:
            headers["transformation"] = "jms-map-xml"
            payload = self.__convert_dict(payload)        
        
        if self.__socket is not None:
            frame = '%s\n%s\n%s\x00' % (command,
                                        reduce(lambda accu, key: accu + ('%s:%s\n' % (key, headers[key])), headers.keys(), ''),
                                        payload)  
            self.__socket_semaphore.acquire()
            try:
                self.__socket.sendall(frame)
            finally:
                self.__socket_semaphore.release()
            log.debug("Sent frame: type=%s, headers=%r, body=%r" % (command, headers, payload))
        else:
            raise NotConnectedException()

    def __notify(self, frame_type, headers=None, body=None):
        for listener in self.__listeners.values():
            if not hasattr(listener, 'on_%s' % frame_type):
                log.debug('listener %s has no method on_%s' % (listener, frame_type))
                continue

            if frame_type == 'connecting':
                listener.on_connecting(self.__current_host_and_port)
                continue

            notify_func = getattr(listener, 'on_%s' % frame_type)
            params = len(notify_func.func_code.co_varnames)
            if params >= 2:
                notify_func(headers, body)
            elif params == 1:
                notify_func(headers)
            else:
                notify_func()

    def __receiver_loop(self):
        """
        Main loop listening for incoming data.
        """
        try:
            try:
                threading.currentThread().setName("StompReceiver")
                while self.__running:
                    log.debug('starting receiver loop')

                    if self.__socket is None:
                        break

                    try:
                        try:
                            self.__notify('connecting')
                            
                            while self.__running:
                                frames = self.__read()
                                
                                for frame in frames:
                                    (frame_type, headers, body) = self.__parse_frame(frame)
                                    log.debug("Received frame: result=%r, headers=%r, body=%r" % (frame_type, headers, body))
                                    frame_type = frame_type.lower()
                                    
                                    if frame_type in [ 'connected', 'message', 'receipt', 'error' ]:
                                        self.__notify(frame_type, headers, body)
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
                            self.__notify('disconnected')
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
    

    def __transform(self, body, transType):
        """
        Perform body transformation. Currently, the only supported transformation is
        'jms-map-xml', which converts a map into python dictionary. This can be extended
        to support other transformation types.

        The body has the following format: 
        <map>
          <entry>
            <string>name</string>
            <string>Dejan</string>
          </entry>
          <entry>
            <string>city</string>
            <string>Belgrade</string>
          </entry>
        </map>

        (see http://docs.codehaus.org/display/STOMP/Stomp+v1.1+Ideas)
        """

        if transType != 'jms-map-xml':
            return body

        try:
            entries = {}
            doc = xml.dom.minidom.parseString(body)
            rootElem = doc.documentElement
            for entryElem in rootElem.getElementsByTagName("entry"):
                pair = []
                for node in entryElem.childNodes:
                    if not isinstance(node, xml.dom.minidom.Element): continue
                    pair.append(node.firstChild.nodeValue)
                assert len(pair) == 2
                entries[pair[0]] = pair[1]
            return entries
        except Exception, ex:
            # unable to parse message. return original
            return body
        

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

        if 'transformation' in headers:
            body = self.__transform(body, headers['transformation'])

        return (frame_type, headers, body)

    def __attempt_connection(self):
        """
        Try connecting to the (host, port) tuples specified at construction time.
        """

        sleep_exp = 1
        while self.__running and self.__socket is None:
            for host_and_port in self.__host_and_ports:
                try:
                    log.debug("Attempting connection to host %s, port %s" % host_and_port)
                    self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    if self.__ssl: # wrap socket
                        if self.__ssl_ca_certs:
                            cert_validation = ssl.CERT_REQUIRED
                        else:
                            cert_validation = ssl.CERT_NONE
                        self.__socket = ssl.wrap_socket(self.__socket, 
                                keyfile=self.__ssl_key_file,
                                certfile=self.__ssl_cert_file,
                                cert_reqs=cert_validation, ca_certs=self.__ssl_ca_certs,
                                ssl_version=ssl.PROTOCOL_SSLv3
                                )
                    self.__socket.settimeout(None)
                    self.__socket.connect(host_and_port)
                    if self.__ssl and self.__ssl_cert_validator: # Validate server cert
                        cert = self.__socket.getpeercert()
                        (ok, errmsg) = apply(self.__ssl_cert_validator, (cert, host_and_port[0]))
                        if not ok:
                            raise SSLError("Server certificate validation failed: %s"%errmsg)
                    self.__current_host_and_port = host_and_port
                    log.info("Established connection to host %s, port %s" % host_and_port)
                    break
                except SSLError:
                    raise
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

                if sleep_duration < self.__reconnect_sleep_max:
                    sleep_exp += 1


#
# command line testing
#
if __name__ == '__main__':
    import cli
    cli.main()
