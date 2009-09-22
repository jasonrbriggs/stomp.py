"""Stomp Protocol Connectivity

    This provides basic connectivity to a message broker supporting the 'stomp' protocol.
    At the moment ACK, SEND, SUBSCRIBE, UNSUBSCRIBE, BEGIN, ABORT, COMMIT, CONNECT and DISCONNECT operations
    are supported.

    This changes the previous version which required a listener per subscription -- now a listener object
    just calls the 'addlistener' method and will receive all messages sent in response to all/any subscriptions.
    (The reason for the change is that the handling of an 'ack' becomes problematic unless the listener mechanism
    is decoupled from subscriptions).

    Note that you must 'start' an instance of Connection to begin receiving messages.  For example:

        conn = stomp.Connection([('localhost', 62003)], 'myuser', 'mypass')
        conn.start()

    Meta-Data
    ---------
    Author: Jason R Briggs
    License: http://www.apache.org/licenses/LICENSE-2.0
    Start Date: 2005/12/01
    Last Revision Date: $Date: 2008/09/11 00:16 $

    Notes/Attribution
    -----------------
    * uuid method courtesy of Carl Free Jr:
      http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/213761
    * patch from Andreas Schobel
    * patches from Julian Scheid of Rising Sun Pictures (http://open.rsp.com.au)
    * patch from Fernando
    * patches from Eugene Strulyov

"""

__version__ = '2.0.4'
__all__ = [ 'stomp' ]

import stomp
import cli
import listener

Connection = stomp.Connection
ConnectionListener = listener.ConnectionListener
StatsListener = listener.StatsListener