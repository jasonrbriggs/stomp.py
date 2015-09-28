===========
Quick start
===========

Stomp.py is a Python library providing access to a message broker using the `STOMP protocol <https://stomp.github.io>`_ - either programmatically or using a command line client.


Stomp.py API
============

::

    >>> import time
    >>> import sys
    >>> 
    >>> import stomp
    >>> 
    >>> class MyListener(stomp.ConnectionListener):
    >>>     def on_error(self, headers, message):
    >>>         print('received an error "%s"' % message)
    >>>     def on_message(self, headers, message):
    >>>         print('received a message "%s"' % message)

    >>> conn = stomp.Connection()
    >>> conn.set_listener('', MyListener())
    >>> conn.start()
    >>> conn.connect('admin', 'password', wait=True)
    >>> 
    >>> conn.subscribe(destination='/queue/test', id=1, ack='auto')
    >>> 
    >>> conn.send(body=' '.join(sys.argv[1:]), destination='/queue/test')
    >>> 
    >>> time.sleep(2)
    >>> conn.disconnect()
    

Command-line Client
===================

Assuming stomp.py is installed (using pip) in the site-packages directory (e.g. lib/python3.3/site-packages), hereby referred to as ${SITEPACKAGES}, then you can run the command line client as follows::

    python ${SITEPACKAGES}/stomp -H localhost -P 61613
    
As of version 4.0.3, a stomp.py is also installed into the bin dir (at least on unix), so you can also run::

    stomp -H localhost -P 61613
    
After a successful connection, you can type commands such as::

    subscribe /queue/test
    send /queue/test hello world
    
If you need to pass a username and password to the client::

    python ${SITEPACKAGES}/stomp -H localhost -P 61613 -U admin -W password
    stomp -H localhost -P 61613 -U admin -W password
    
Type help for more information once you're running the command-line interface, or run the following to see the list of startup arguments::

    python ${SITEPACKAGES}/stomp --help
    stomp --help