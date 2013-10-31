##@namespace stomp.backward3
# Python3-specific versions of various functions used by stomp.py


def input_prompt(prompt):
    """
    Get user input
    """
    return input(prompt)

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
    return b''.join(encoded_pieces)

NULL = b'\x00'

def join(chars):
    return b''.join(chars).decode('UTF-8')

def getheader(headers, key):
    return headers[key]


