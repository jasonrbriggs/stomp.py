#
# Functions for backwards compatibility
#

def input_prompt(prompt):
    """
    Get user input
    """
    return raw_input(prompt)

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
    return ''.join(chars)

def getheader(headers, key):
    return headers.getheader(key)

def wrap_stringio(sio):
    import codecs
    return codecs.getwriter("utf8")(sio)        
