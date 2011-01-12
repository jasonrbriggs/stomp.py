import sys

#
# Functions for backwards compatibility
#

def get_func_argcount(func):
    """
    Return the argument count for a function
    """
    if sys.hexversion > 0x03000000:
        return func.__code__.co_argcount
    else:
        return func.func_code.co_argcount
        
def input_prompt(prompt):
    """
    Get user input
    """
    if sys.hexversion > 0x03000000:
        return input(prompt)
    else:
        return raw_input(prompt)
        
def join(chars):
    if sys.hexversion > 0x03000000:
        return bytes('', 'UTF-8').join(chars).decode('UTF-8')
    else:
        return ''.join(chars)

def socksend(conn, msg):
    if sys.hexversion > 0x03000000:
        conn.send(msg.encode())
    else:
        conn.send(msg)
        
        
def getheader(headers, key):
    if sys.hexversion > 0x03000000:
        return headers[key]
    else:
        return headers.getheader(key)
        

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