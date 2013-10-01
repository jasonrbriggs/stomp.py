import re
import threading
import xml.dom

try:
    import hashlib
except ImportError:
    import md5 as hashlib


# List of all host names (unqualified, fully-qualified, and IP
# addresses) that refer to the local host (both loopback interface
# and external interfaces).  This is used for determining
# preferred targets.
LOCALHOST_NAMES = [ "localhost", "127.0.0.1" ]

try:
    LOCALHOST_NAMES.append(socket.gethostbyname(socket.gethostname()))
except:
    pass
    
try:
    LOCALHOST_NAMES.append(socket.gethostname())
except:
    pass
    
try:
    LOCALHOST_NAMES.append(socket.getfqdn(socket.gethostname()))
except:
    pass

#
# Used to parse STOMP header lines in the format "key:value",
#
HEADER_LINE_RE = re.compile('(?P<key>[^:]+)[:](?P<value>.*)')


def default_create_thread(callback):
    """
    Default thread creation
    """
    thread = threading.Thread(None, callback)
    thread.daemon = True  # Don't let receiver thread prevent termination
    thread.start()
    return thread


def is_localhost(host_and_port):
    """
    Return true if the specified host+port is a member of the 'localhost' list of hosts
    """
    (host, port) = host_and_port
    if host in LOCALHOST_NAMES:
        return 1
    else:
        return 2


def parse_headers(lines, offset=0):
    headers = {}
    for header_line in lines[offset:]:
        header_match = HEADER_LINE_RE.match(header_line)
        if header_match:
            key = header_match.group('key')
            if key not in headers:
                headers[key] = header_match.group('value')
    return headers


def parse_frame(frame):
    """
    Parse a STOMP frame into a (frame_type, headers, body) tuple,
    where frame_type is the frame type as a string (e.g. MESSAGE),
    headers is a map containing all header key/value pairs, and
    body is a string containing the frame's payload.
    """
    f = Frame()
    if frame == '\x0a':
        f.cmd = 'heartbeat'
        return f
        
    preamble_end = frame.find('\n\n')
    if preamble_end == -1:
        preamble_end = len(frame)
    preamble = frame[0:preamble_end]
    preamble_lines = preamble.split('\n')
    f.body = frame[preamble_end + 2:]

    # Skip any leading newlines
    first_line = 0
    while first_line < len(preamble_lines) and len(preamble_lines[first_line]) == 0:
        first_line += 1

    # Extract frame type/command
    f.cmd = preamble_lines[first_line]

    # Put headers into a key/value map
    f.headers = parse_headers(preamble_lines, first_line + 1)

    #if 'transformation' in headers:
    #    body = transform(body, headers['transformation'])

    return f

    
def transform(body, trans_type):
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
    
    \param body the content of a message
    
    \param trans_type the type transformation
    """
    if trans_type != 'jms-map-xml':
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
    except Exception:
        #
        # unable to parse message. return original
        #
        return body

    
def merge_headers(header_map_list):
    """
    Helper function for combining multiple header maps into one.
    """
    headers = {}
    for header_map in header_map_list:
        for header_key in header_map.keys():
            headers[header_key] = header_map[header_key]
    return headers

    
def calculate_heartbeats(shb, chb):
    """
    Given a heartbeat string from the server, and a heartbeat tuple from the client,
    calculate what the actual heartbeat settings should be.
    """
    (sx, sy) = shb
    (cx, cy) = chb
    x = 0
    y = 0
    if cx != 0 and sy != '0':
        x = max(cx, int(sy))
    if cy != 0 and sx != '0':
        y = max(cy, int(sx))
    return (x, y)

    
class Frame:
    def __init__(self, cmd = None, headers = {}, body = None):
        self.cmd = cmd
        self.headers = headers
        self.body = body
