=============
Using the API
=============

Establishing a connection
-------------------------

The simplest way to establish a connection, assuming the message broker is running on the local machine, is::

    >>> import stomp
    >>> c = stomp.Connection([('127.0.0.1', 62613)])
    >>> c.start()
    >>> c.connect('admin', 'password', wait=True)
    
By default this represents a STOMP 1.1 connection. You can request a specific version of the connection using one of the following::

    >>> c = stomp.Connection10([('127.0.0.1', 62613)])
    >>> c = stomp.Connection11([('127.0.0.1', 62613)])
    >>> c = stomp.Connection12([('127.0.0.1', 62613)])

The first parameter to a ``Connection`` is ``host_and_ports``. This is a list of tuples, each containing ip address (which could be an ipv6 address) and the port where the message broker is listening for stomp connections. The general idea with the list is to try each address until a successful socket connection is established (giving the ability to provide multiple brokers for failover).

An example of setting up a connection with failover addresses might be::

    >>> import stomp
    >>> c = stomp.Connection([('192.168.1.100', 61613), ('192.168.1.101', 62613)])
    
And here's an example of an ipv6 connection::

    >>> import stomp
    >>> c = stomp.Connection(['fe80::a00:27ff:fe90:3f1a%en1', 62613])
    
There are a number of other parameters for initialising the connection (looking at the StompConnection12 class):

    .. autoclass:: stomp.connect.StompConnection12

The ``start`` method is next - which performs the actual socket connection to the remote server and starts a separate receiver thread. The final step is to call the ``connect`` method (corresponding to the `CONNECT frame <https://stomp.github.io/stomp-specification-1.2.html#CONNECT_or_STOMP_Frame>`_):

    .. automethod:: stomp.protocol.Protocol12.connect

Note that connect also allows for a map (dict) of headers to be provided, and will merge these with any additional named parameters to build the headers for the `STOMP frame <https://stomp.github.io/stomp-specification-1.2.html#STOMP_Frames>`_, allowing for non-standard headers to be transmitted to the broker. 

Sending and receiving messages
------------------------------

Once the connection is established, you can send messages using the ``send`` method:

    .. automethod:: stomp.protocol.Protocol12.send
    
To receive messages back from the messaging system, you need to setup some sort of listener on your connection, and then subscribe to the destination (see `STOMP subscribe <https://stomp.github.io/stomp-specification-1.2.html#SUBSCRIBE>`_). Listeners are simply a subclass which implements the methods in the ConnectionListener class (see `this page <stomp.html#module-stomp.listener>`_ for more detail). Stomp provides a few implementations of listeners, but the simplest is ``PrintingListener`` which just prints all interactions between the client and server. A simple example of this in action is::

    >>> from stomp import *
    >>> c = Connection([('127.0.0.1', 62613)])
    >>> c.set_listener('', PrintingListener())
    >>> c.start()
    >>> c.connect('admin', 'password', wait=True)
    on_connecting 127.0.0.1 62613
    on_send STOMP {'passcode': 'password', 'login': 'admin', 'accept-version': '1.2', 'host': '127.0.0.1'}
    on_connected {'server': 'apache-apollo/1.7.1', 'host-id': 'mybroker', 'session': 'mybroker-13e0', 'heart-beat': '100,10000', 'version': '1.2', 'user-id': 'admin'}
    >>> c.subscribe('/queue/test', 123)
    on_send SUBSCRIBE {'id': 123, 'ack': 'auto', 'destination': '/queue/test'}
    >>> c.send('/queue/test', 'a test message')
    on_send SEND {'content-length': 5, 'destination': '/queue/test'} b'a test message'
    >>> on_before_message {'destination': '/queue/test', 'message-id': 'mybroker-13e01', 'subscription': '123', 'ack': '2', 'content-length': '5'} a test message
    on_message {'destination': '/queue/test', 'message-id': 'mybroker-13e01', 'subscription': '123', 'ack': '2', 'content-length': '5'} a test message
    
You can see the responses from the message system in the ``on_connected``, and ``on_message`` output. The stomp frames sent to the server can be seen in each ``on_send`` output (an initial STOMP connect frame, SUBSCRIBE and then SEND).

In the case of the subscribe method, as of STOMP 1.1, the ``id`` parameter is required (if connecting with STOMP 1.0, only the destination is required):

    .. automethod:: stomp.protocol.Protocol12.subscribe
    
Note that listeners can be named so you can use more that one type of listener at the same time::

    >>> c.set_listener('stats', StatsListener())
    >>> c.set_listener('print', PrintingListener())
    
You unsubscribe from a topic or queue using the unique ``id`` for the subscription::

    >>> c.subscribe('/queue/test', 123)
    >>> c.unsubscribe(123)


Acks and Nacks
--------------

Acknowledgements are a way to tell the message server that a message was either consumed, or not. Assume a collection of clients on a server listening on a queue, and a message which requires significant processing. One of the clients receives the message, checks resource usage on the server and decides to send a nack as a consequence. The message server could, at that point, decide to send to a failover server for processing (that's a possible use, anyway).

Use the client or client-individual acknowledgement parameter (see `here <https://stomp.github.io/stomp-specification-1.2.html#SUBSCRIBE_ack_Header>`_ for a description) with the subscription, in order to use acks and nacks. Afterwards, you use the message and subscription ids to ack or nack the message::

    >>> conn.subscribe('/queue/test', id=4, ack='client')
    on_before_message {'message-id': 'mybroker-14aa2', 'destination': '/queue/test', 'subscription': '4', 'content-length': '14'} test message 1
    on_message {'message-id': 'mybroker-14aa2', 'destination': '/queue/test', 'subscription': '4', 'content-length': '14'} test message 1
    >>> conn.ack('mybroker-14aa2', 2)
    
    on_before_message {'message-id': 'mybroker-14ab2', 'destination': '/queue/test', 'subscription': '4', 'content-length': '14'} test message 2
    on_message {'message-id': 'mybroker-14ab2', 'destination': '/queue/test', 'subscription': '4', 'content-length': '14'} test message 2
    >>> conn.nack('mybroker-14ab2', 2)


Transactions
------------

The STOMP protocol provides a way to transmit messages to a broker inside a transaction, which are held on the server until the transaction is either committed - at which point they're sent - or aborted - where the messages are discarded.

Begin a transaction using the ``begin`` method, which returns the transaction id you then use when sending messages (you can also generate your own transaction id and pass that as a parameter to ``begin``)::

    >>> conn.subscribe('/queue/test', id=5)
    >>> txid = conn.begin()
    >>> conn.send('/queue/test', 'test1', transaction=txid)
    >>> conn.send('/queue/test', 'test2', transaction=txid)
    >>> conn.send('/queue/test', 'test3', transaction=txid)
    >>> conn.commit(txid)
    
    on_message {'subscription': '5', 'content-length': '5', 'destination': '/queue/test', 'message-id': 'mybroker-14b03', 'transaction': 'b39f3136-46a3-4e11-8ba8-845e36d48412'} test1
    on_message {'subscription': '5', 'content-length': '5', 'destination': '/queue/test', 'message-id': 'mybroker-14b04', 'transaction': 'b39f3136-46a3-4e11-8ba8-845e36d48412'} test2
    on_message {'subscription': '5', 'content-length': '5', 'destination': '/queue/test', 'message-id': 'mybroker-14b05', 'transaction': 'b39f3136-46a3-4e11-8ba8-845e36d48412'} test3
    
Abort a transaction (and discard the sent messages using ``abort``):

    >>> conn.subscribe('/queue/test', id=6)
    >>> txid = conn.begin()
    >>> conn.send('/queue/test', 'test4', transaction=txid)
    >>> conn.send('/queue/test', 'test5', transaction=txid)
    >>> conn.abort(txid)

    
Disconnect
----------

Stomp.py supports graceful shutdown/disconnections through a receipt parameter (automatically generated if you don't provide it). The connection is only dropped when the server sends back a response to that receipt::

    >>> conn.disconnect()
    on_send DISCONNECT {'receipt': '825a5cd6-9e3c-4a72-8051-72348a94f5ce'}
    on_receipt {'receipt-id': '825a5cd6-9e3c-4a72-8051-72348a94f5ce'}
    on_disconnected    

