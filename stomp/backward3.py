"""
Python3-specific versions of various functions used by stomp.py
"""

NULL = b'\x00'


def input_prompt(prompt):
    """
    Get user input

    :param str prompt: the prompt to display to the user

    :rtype: str
    """
    return input(prompt)


def decode(byte_data, encoding='utf-8'):
    """
    Decode the byte data to a string if not None.

    :param bytes byte_data: the data to decode

    :rtype: str
    """
    if byte_data is None:
        return None
    return byte_data.decode(encoding, errors='replace')


def encode(char_data, encoding='utf-8'):
    """
    Encode the parameter as a byte string.

    :param char_data: the data to encode

    :rtype: bytes
    """
    if type(char_data) is str:
        return char_data.encode(encoding, errors='replace')
    elif type(char_data) is bytes:
        return char_data
    else:
        raise TypeError('message should be a string or bytes, found %s' % type(char_data))


def pack(pieces=()):
    """
    Join a sequence of strings together.

    :param list pieces: list of strings

    :rtype: bytes
    """
    return b''.join(pieces)


def join(chars=()):
    """
    Join a sequence of characters into a string.

    :param bytes chars: list of chars

    :rtype: str
    """
    return b''.join(chars).decode()
