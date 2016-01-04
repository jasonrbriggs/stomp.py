"""
Python2-specific versions of various functions used by stomp.py
"""

NULL = '\x00'


def input_prompt(prompt):
    """
    Get user input
    """
    return raw_input(prompt)


def decode(byte_data):
    """
    Decode the byte data to a string - in the case of this Py2 version, we can't really do anything (Py3 differs).
    """
    return byte_data  # no way to know if it's unicode or not, so just pass through unmolested


def encode(char_data):
    """
    Encode the parameter as a byte string.
    """
    if type(char_data) is unicode:
        return char_data.encode('utf-8')
    else:
        return char_data


def pack(pieces=[]):
    """
    Join a list of strings together (note: py3 version differs)
    """
    return ''.join(encode(p) for p in pieces)


def join(chars=[]):
    """
    Join a list of characters into a string.
    """
    return ''.join(chars)
