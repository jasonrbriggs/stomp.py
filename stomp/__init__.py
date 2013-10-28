"""
This provides connectivity to a message broker supporting the STOMP protocol. Both protocol
versions 1.0 and 1.1 are supported.

See the GITHUB project page for more information.

Author: Jason R Briggs
License: http://www.apache.org/licenses/LICENSE-2.0
Project Page: https://github.com/jasonrbriggs/stomp.py
"""

import os
import sys
sys.path.insert(0, os.path.split(__file__)[0])

import connect, listener, exception, transport, protocol

__version__ = (4, 0, 2)
Connection10 = connect.StompConnection10
Connection11 = connect.StompConnection11
Connection12 = connect.StompConnection12
Connection = connect.StompConnection11
ConnectionListener = listener.ConnectionListener
StatsListener = listener.StatsListener
