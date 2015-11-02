"""
Python3-specific versions of various functions used by stomp.py
"""

NULL = b'\x00'


def input_prompt(prompt):
    """
    Get user input

    :param prompt: the prompt to display to the user
    """
    return input(prompt)


def decode(byte_data):
    """
    Decode the byte data to a string if not None.

    :param byte_data: the data to decode
    """
    if byte_data is None:
        return None
    return byte_data.decode()


def encode(char_data):
    """
    Encode the parameter as a byte string.

    :param char_data: the data to encode
    """
    if type(char_data) is str:
        return char_data.encode()
    elif type(char_data) is bytes:
        return char_data
    else:
        raise TypeError('message should be a string or bytes')


def pack(pieces=[]):
    """
    Join a list of strings together.

    :param pieces: list of strings
    """
    encoded_pieces = (encode(piece) for piece in pieces)
    return b''.join(encoded_pieces)


def join(chars=[]):
    """
    Join a list of characters into a string.

    :param chars: list of chars
    """
    return b''.join(chars).decode()
