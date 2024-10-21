"""stomp.py provides connectivity to a message broker supporting the STOMP protocol.
Protocol versions 1.0, 1.1 and 1.2 are supported.

See the GITHUB project page for more information.

Author: Jason R Briggs |br|
License: http://www.apache.org/licenses/LICENSE-2.0 |br|
Project Page: https://github.com/jasonrbriggs/stomp.py

"""

import stomp.adapter as adapter
import stomp.connect as connect
import stomp.listener as listener
import stomp.logging as logging

__version__ = "8.2.0"

##
# Alias for STOMP 1.0 connections.
#
Connection10 = connect.StompConnection10
StompConnection10 = Connection10

##
# Alias for STOMP 1.1 connections.
#
Connection11 = connect.StompConnection11
StompConnection11 = Connection11

##
# Alias for STOMP 1.2 connections.
#
Connection12 = connect.StompConnection12
StompConnection12 = Connection12
WSConnection = adapter.ws.WSStompConnection
WSStompConnection = WSConnection

##
# Default connection alias (STOMP 1.1).
#
Connection = connect.StompConnection11

##
# Access to the default connection listener.
#
ConnectionListener = listener.ConnectionListener

##
# Access to the stats listener.
#
StatsListener = listener.StatsListener

##
# Access to the 'waiting' listener.
WaitingListener = listener.WaitingListener

##
# Access to the printing listener
PrintingListener = listener.PrintingListener

def tuple_version():
    global __version__
    if type(__version__) != tuple:
        import re
        __version__ = tuple([int(x) for x in re.sub("[^0-9.]", "", __version__).split(".")])