import sys

##@namespace stomp.backward
# Functions to support backwards compatibility.
#
# Basically where we have functions which differ between python 2 and 3, we provide implementations here
# and then Python-specific versions in backward2 and backward3.

if sys.hexversion >= 0x03000000: # Python 3+
    from stomp.backward3 import *
else: # Python 2
    from stomp.backward2 import *


def get_errno(e):
    """
    Return the errno of an exception, or the first argument if errno is not available.
    """
    try:
        return e.errno
    except AttributeError:
        return e.args[0]


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
