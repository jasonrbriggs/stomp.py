try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5
import time
import random

def _uuid( *args ):
    """
    uuid courtesy of Carl Free Jr:
    (http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/213761)
    """

    t = long( time.time() * 1000 )
    r = long( random.random() * 100000000000000000L )

    try:
        a = socket.gethostbyname( socket.gethostname() )
    except:
        # if we can't get a network address, just imagine one
        a = random.random() * 100000000000000000L
    data = str(t) + ' ' + str(r) + ' ' + str(a) + ' ' + str(args)
    md5 = md5()
    md5.update(data)
    data = md5.hexdigest()
    return data


class DevNullLogger(object):
    """
    dummy logging class for environments without the logging module
    """
    def log(self, msg):
        print msg

    def devnull(self, msg):
        pass

    debug = devnull
    info = devnull
    warning = log
    error = log
    critical = log
    exception = log

    def isEnabledFor(self, lvl):
        return False
