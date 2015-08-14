##@namespace stomp.backward3
# Python3-specific versions of various functions used by stomp.py

NULL = b'\x00'


def input_prompt(prompt):
    """
    Get user input
    """
    return input(prompt)


def decode(byte_data):
    if byte_data is None:
        return None
    return byte_data.decode()


def encode(char_data):
    if type(char_data) is str:
        return char_data.encode()
    elif type(char_data) is bytes:
        return char_data
    else:
        raise TypeError('message should be a string or bytes')


def pack(pieces):
    encoded_pieces = (encode(piece) for piece in pieces)
    return b''.join(encoded_pieces)


def join(chars):
    return b''.join(chars).decode()


def getheader(headers, key):
    return headers[key]
