import hashlib
import time
import random

def _uuid( *args ):
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


class DevNullLogger(object):
    """
    Dummy logging class for environments without the logging module
    """
    def log(self, msg):
        """
        Log a message (print to console)
        """
        print(msg)

    def devnull(self, msg):
        """
        Dump a message (i.e. send to /dev/null)
        """
        pass

    debug = devnull
    info = devnull
    warning = log
    error = log
    critical = log
    exception = log

    def isEnabledFor(self, lvl):
        """
        Always return False
        """
        return False
