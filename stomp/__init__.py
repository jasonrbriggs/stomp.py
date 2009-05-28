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

    Updates
    -------
    * 2007/03/31 : (Andreas Schobel) patch to fix newlines problem in ActiveMQ 4.1
    * 2007/09    : (JRB) updated to get stomp.py working in Jython as well as Python
    * 2007/09/05 : (Julian Scheid) patch to allow sending custom headers
    * 2007/09/18 : (JRB) changed code to use logging instead of just print. added logger for jython to work
    * 2007/09/18 : (Julian Scheid) various updates, including:
       - change incoming message handling so that callbacks are invoked on the listener not only for MESSAGE, but also for
            CONNECTED, RECEIPT and ERROR frames.
       - callbacks now get not only the payload but any headers specified by the server
       - all outgoing messages now sent via a single method
       - only one connection used
       - change to use thread instead of threading
       - sends performed on the calling thread
       - receiver loop now deals with multiple messages in one received chunk of data
       - added reconnection attempts and connection fail-over
       - changed defaults for "user" and "passcode" to None instead of empty string (fixed transmission of those values)
       - added readline support
    * 2008/03/26 : (Fernando) added cStringIO for faster performance on large messages
    * 2008/09/10 : (Eugene) remove lower() on headers to support case-sensitive header names
    * 2008/09/11 : (JRB) fix incompatibilities with RabbitMQ, add wait for socket-connect
    * 2008/10/28 : (Eugene) add jms map (from stomp1.1 ideas)
    * 2008/11/25 : (Eugene) remove superfluous (incorrect) locking code
    * 2009/02/05 : (JRB) remove code to replace underscores with dashes in header names (causes a problem in rabbit-mq)
    * 2009/03/29 : (JRB) minor change to add logging config file
                   (JRB) minor change to add socket timeout, suggested by Israel
    * 2009/04/01 : (Gavin) patch to change md5 to hashlib (for 2.6 compatibility)
    * 2009/04/02 : (Fernando Ciciliati) fix overflow bug when waiting too long to connect to the broker
    * 2009/05/28 : (Martin Pieuchot) patch to support version of Python pre 2.5

"""

__version__ = '2.0.1'
__all__ = [ 'stomp' ]

import stomp
import cli
import listener

Connection = stomp.Connection
ConnectionListener = listener.ConnectionListener
StatsListener = listener.StatsListener