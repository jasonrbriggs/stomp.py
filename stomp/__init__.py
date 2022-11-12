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

__version__ = (9, 0, 0)


##
# Default connection alias (STOMP 1.1).
#
Connection = connect.StompConnection11
Connection10 = connect.StompConnection10
Connection11 = connect.StompConnection11
Connection12 = connect.StompConnection12
