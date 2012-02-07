import sys
import time
import random
import socket
import hashlib

#
# Functions for backwards compatibility
#

if sys.hexversion >= 0x03000000: # Python 3
    from backward3 import *
else: # Python 2
    from backward2 import *

def socksend(conn, msg):
    conn.sendall(encode(msg))
        
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
