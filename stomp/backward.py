import sys
import time
import random
import socket
import hashlib

#
# Functions for backwards compatibility
#

def input_prompt(prompt):
    """
    Get user input
    """
    if sys.hexversion >= 0x03000000:
        return input(prompt)
    else:
        return raw_input(prompt)

if sys.hexversion >= 0x03000000: # Python 3

    def decode(byte_data):
        return byte_data.decode('utf-8')

    def encode(char_data):
        if type(char_data) is str:
            return char_data.encode()
        elif type(char_data) is bytes:
            return char_data
        else:
            raise TypeError('message should be a string or bytes')

    def hasbyte(byte, byte_data):
        assert type(byte) is int and 0 <= byte and byte < 2**8
        return bytes([byte]) in byte_data

    def pack(pieces):
        encoded_pieces = (encode(piece) for piece in pieces)
        return sum(encoded_pieces, bytes())

    NULL = bytes([0]) 

else: # Python 2

    def decode(byte_data):
        return byte_data # no way to know if it's unicode or not, so just pass through unmolested

    def encode(char_data):
        if type(char_data) is unicode:
            return char_data.encode('utf-8')
        else:
            return char_data

    def hasbyte(byte, byte_data):
        return chr(byte) in byte_data

    def pack(pieces):
        return ''.join(pieces)

    NULL = '\x00'

def join(chars):
    if sys.hexversion >= 0x03000000:
        return bytes('', 'UTF-8').join(chars).decode('UTF-8')
    else:
        return ''.join(chars)

def socksend(conn, msg):
    conn.sendall(encode(msg))
        
        
def getheader(headers, key):
    if sys.hexversion >= 0x03000000:
        return headers[key]
    else:
        return headers.getheader(key)

def wrap_stringio(sio):
    if sys.hexversion >= 0x03000000:
        return sio
    else:
        import codecs
        return codecs.getwriter("utf8")(sio)        

class uuid(object):
    def uuid4(*args):
        """
        uuid courtesy of Carl Free Jr:
        (http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/213761)
        """
        t = int(time.time() * 1000)
        r = int(random.random() * 100000000000000000)

        try:
            a = socket.gethostbyname( socket.gethostname() )
        except:
            # if we can't get a network address, just imagine one
            a = random.random() * 100000000000000000
        data = str(t) + ' ' + str(r) + ' ' + str(a) + ' ' + str(args)
        md5 = hashlib.md5()
        md5.update(data.encode())
        data = md5.hexdigest()
        return data

def gcd(a, b):
    """Calculate the Greatest Common Divisor of a and b.

    Unless b==0, the result will have the same sign as b (so that when
    b is divided by it, the result comes out positive).
    
    Copied from the Python2.6 source
    Copyright (c) 2001-2011 Python Software Foundation; All Rights Reserved
    """
    while b:
        a, b = b, a%b
    return a
