===========
Quick start
===========

Stomp.py is a Python library providing access to a message broker using the `STOMP protocol <https://stomp.github.io>`_ - either programmatically or using a command line client.


Installation
============

Stomp is available on `PyPi <https://pypi.org/project/stomp.py/>`_. Install it in a new environment using virtualenv and pip:

.. code-block:: shell

    $ virtualenv -p python3 teststomp
    $ . teststomp/bin/activate
    (teststomp) $ pip install stomp.py
    (teststomp) $ stomp --version


Stomp.py API
============

A simple example of creating a listener, sending and receiving a message using localhost with the default port (61613), can be seen here::

    import time
    import sys
    
    import stomp
    
    class MyListener(stomp.ConnectionListener):
        def on_error(self, headers, message):
            print('received an error "%s"' % message)
        def on_message(self, headers, message):
            print('received a message "%s"' % message)

    conn = stomp.Connection()
    conn.set_listener('', MyListener())
    conn.connect('admin', 'password', wait=True)
    conn.subscribe(destination='/queue/test', id=1, ack='auto')
    conn.send(body=' '.join(sys.argv[1:]), destination='/queue/test')
    time.sleep(2)
    conn.disconnect()

Assuming this was saved to stomptest.py, the code can be executed as follows:

.. code-block:: shell

    $ python stomptest.py This is a test
    received a message "This is a test"


Command-line Client
===================

Assuming stomp.py is installed (using pip) in the site-packages directory (e.g. lib/python3.3/site-packages), hereby referred to as ${SITEPACKAGES}, then you can run the command line client as follows:

.. code-block:: shell

    $ stomp -H localhost -P 61613
        
After a successful connection, you can type commands such as:

.. code-block:: shell

    subscribe /queue/test
    send /queue/test hello world
    
If you need to pass a username and password to the client:

.. code-block:: shell

    $ stomp -H localhost -P 61613 -U admin -W password
    
Type help for more information once you're running the command-line interface, or run the following to see the list of startup arguments:

.. code-block:: shell

    $ stomp --help

