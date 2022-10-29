"""General utility functions.
"""
import asyncio
import copy
import os
import re
import socket
import threading
import uuid

from stomp.constants import *

# List of all host names (unqualified, fully-qualified, and IP
# addresses) that refer to the local host (both loopback interface
# and external interfaces).  This is used for determining
# preferred targets.
LOCALHOST_NAMES = ["localhost", "127.0.0.1"]

NULL = b"\x00"

if not os.environ.get("STOMP_SKIP_HOSTNAME_SCAN"):
    try:
        LOCALHOST_NAMES.append(socket.gethostbyname(socket.gethostname()))
    except Exception:
        pass

    try:
        LOCALHOST_NAMES.append(socket.gethostname())
    except Exception:
        pass

    try:
        LOCALHOST_NAMES.append(socket.getfqdn(socket.gethostname()))
    except Exception:
        pass


def decode(byte_data, encoding="utf-8"):
    """
    Decode the byte data to a string if not None.

    :param bytes byte_data: the data to decode
    :param string encoding: character encoding

    :rtype: str
    """
    if byte_data is None:
        return None
    return byte_data.decode(encoding, errors="replace")


def encode(char_data, encoding="utf-8"):
    """
    Encode the parameter as a byte string.

    :param char_data: the data to encode
    :param string encoding: character encoding

    :rtype: bytes
    """
    if type(char_data) is str:
        return char_data.encode(encoding, errors="replace")
    elif type(char_data) is bytes:
        return char_data
    else:
        raise TypeError("message should be a string or bytes, found %s" % type(char_data))


def pack(pieces=()):
    """
    Join a sequence of strings together.

    :param list pieces: list of strings

    :rtype: bytes
    """
    return b"".join(pieces)


def join(chars=()):
    """
    Join a sequence of characters into a string.

    :param bytes chars: list of chars

    :rtype: str
    """
    return b"".join(chars).decode()


def is_eol_default(c):
    return c == b"\x0a"


##
# Used to parse STOMP header lines in the format "key:value",
#
HEADER_LINE_RE = re.compile("(?P<key>[^:]+)[:](?P<value>.*)")

##
# As of STOMP 1.2, lines can end with either line feed, or carriage return plus line feed.
#
PREAMBLE_END_RE = re.compile(b"\n\n|\r\n\r\n")

##
# As of STOMP 1.2, lines can end with either line feed, or carriage return plus line feed.
#
LINE_END_RE = re.compile("\n|\r\n")

##
# Used to replace the "passcode" to be dumped in the transport log (at debug level)
#
PASSCODE_RE = re.compile(r"passcode:\s+[^\' ]+")

ENC_NEWLINE = encode("\n")
ENC_NULL = encode(NULL)


def default_create_thread(callback):
    """
    Default thread creation - used to create threads when the client doesn't want to provide their
    own thread creation.

    :param function callback: the callback function provided to threading.Thread
    """
    thread = threading.Thread(None, callback)
    thread.daemon = True  # Don't let thread prevent termination
    thread.start()
    return thread


def is_localhost(host_and_port):
    """
    Return 1 if the specified host+port is a member of the 'localhost' list of hosts, 2 if not (predominately used
    as a sort key.

    :param (str,int) host_and_port: tuple containing host and port

    :rtype: int
    """
    (host, _) = host_and_port
    if host in LOCALHOST_NAMES:
        return 1
    return 2


_HEADER_ESCAPES = {
    "\r": "\\r",
    "\n": "\\n",
    ":": "\\c",
    "\\": "\\\\",
}
_HEADER_UNESCAPES = dict((value, key) for (key, value) in _HEADER_ESCAPES.items())


def _unescape_header(matchobj):
    escaped = matchobj.group(0)
    unescaped = _HEADER_UNESCAPES.get(escaped)
    if not unescaped:
        # TODO: unknown escapes MUST be treated as fatal protocol error per spec
        unescaped = escaped
    return unescaped


def _escape_headers(headers):
    """
    :param dict(str,str) headers:
    """
    for key, val in headers.items():
        try:
            val = val.replace("\\", "\\\\").replace("\n", "\\n").replace(":", "\\c").replace("\r", "\\r")
        except:
            pass
        headers[key] = val
    return headers


def parse_headers(lines, offset=0):
    """
    Parse the headers in a STOMP response

    :param list(str) lines: the lines received in the message response
    :param int offset: the starting line number

    :rtype: dict(str,str)
    """
    headers = {}
    for header_line in lines[offset:]:
        header_match = HEADER_LINE_RE.match(header_line)
        if header_match:
            key = header_match.group("key")
            key = re.sub(r"\\.", _unescape_header, key)
            if key not in headers:
                value = header_match.group("value")
                value = re.sub(r"\\.", _unescape_header, value)
                headers[key] = value
    return headers


def parse_frame(frame, auto_decode=True, encoding="utf-8"):
    """
    Parse a STOMP frame into a Frame object.

    :param bytes frame: the frame received from the server (as a byte string)

    :rtype: Frame
    """
    mat = PREAMBLE_END_RE.search(frame)
    if mat:
        preamble_end = mat.start()
        body_start = mat.end()
    else:
        preamble_end = len(frame)
        body_start = preamble_end
    preamble = decode(frame[0:preamble_end])
    preamble_lines = LINE_END_RE.split(preamble)
    preamble_len = len(preamble_lines)
    body = frame[body_start:]
    if auto_decode:
        body = decode(body, encoding)

    # Skip any leading newlines
    first_line = 0
    while first_line < preamble_len and len(preamble_lines[first_line]) == 0:
        first_line += 1

    if first_line >= preamble_len:
        return None

    # Extract frame type/command
    cmd = preamble_lines[first_line]

    # Put headers into a key/value map
    headers = parse_headers(preamble_lines, first_line + 1)

    return Frame(cmd, headers, body)


def merge_headers(*header_map_list):
    """
    Helper function for combining multiple header maps into one.

    :param list(dict) header_map_list: list of maps

    :rtype: dict
    """
    headers = {}
    for header_map in header_map_list:
        if header_map:
            headers.update(header_map)
    return headers


def clean_headers(headers):
    rtn = headers
    if "passcode" in headers:
        rtn = copy.copy(headers)
        rtn["passcode"] = "********"
    return rtn


# lines: lines returned from a call to convert_frames
def clean_lines(lines):
    lines = list(filter(lambda l: l != b'', [l.rstrip() for l in lines]))
    return re.sub(PASSCODE_RE, "passcode:********", str(lines))


def calculate_heartbeats(shb, chb):
    """
    Given a heartbeat string from the server, and a heartbeat tuple from the client,
    calculate what the actual heartbeat settings should be.

    :param (str,str) shb: server heartbeat numbers
    :param (int,int) chb: client heartbeat numbers

    :rtype: (int,int)
    """
    (sx, sy) = shb
    (cx, cy) = chb
    x = 0
    y = 0
    if cx != 0 and sy != "0":
        x = max(cx, int(sy))
    if cy != 0 and sx != "0":
        y = max(cy, int(sx))
    return x, y


def convert_frame(frame, encoding="utf-8"):
    """
    Convert a frame to a list of lines separated by newlines.

    :param Frame frame: the Frame object to convert

    :rtype: list(str)
    """
    lines = []

    body = None
    if frame.body:
        body = encode(frame.body, encoding)

        if HDR_CONTENT_LENGTH in frame.headers:
            frame.headers[HDR_CONTENT_LENGTH] = len(body)

    if frame.cmd:
        lines.append(encode(frame.cmd))
        lines.append(ENC_NEWLINE)

    for key, vals in sorted(_escape_headers(frame.headers).items()):
        if vals is None:
            continue
        if type(vals) != tuple:
            vals = (vals,)
        for val in vals:
            lines.append(encode("%s:%s\n" % (key, val)))
    lines.append(ENC_NEWLINE)
    if body:
        lines.append(body)

    if frame.cmd:
        lines.append(ENC_NULL)
    return lines


def length(s):
    """
    Null (none) safe length function.

    :param str s: the string to return length of (None allowed)

    :rtype: int
    """
    if s is not None:
        return len(s)
    return 0


class Frame(object):
    """
    A STOMP frame (or message).

    :param str cmd: the protocol command
    :param dict headers: a map of headers for the frame
    :param body: the content of the frame.
    """
    def __init__(self, cmd, headers=None, body=None):
        self.cmd = cmd
        self.headers = headers if headers is not None else {}
        self.original_headers = copy.copy(self.headers)
        self.body = body

    def __str__(self):
        return "{cmd=%s,headers=[%s],body=%s}" % (self.cmd, self.headers, self.body)


def get_uuid():
    return str(uuid.uuid4())


def get_errno(e):
    """
    Return the errno of an exception, or the first argument if errno is not available.

    :param Exception e: the exception object
    """
    try:
        return e.errno
    except AttributeError:
        return e.args[0]


def async_run(func, *args):
    print(func, *args)
    asyncio.run(func(*args))

HEARTBEAT_FRAME = Frame("heartbeat")
