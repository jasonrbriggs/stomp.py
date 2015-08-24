import sys

if sys.hexversion < 0x02060000: # < Python 2.6
    from stomp.backwardsock25 import *
else: # Python 2.6 onwards
    from stomp.backwardsock26 import *
