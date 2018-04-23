========
stomp.py
========

.. image:: https://badge.fury.io/py/stomp.py.svg
   :target: https://badge.fury.io/py/stomp.py
   :alt: PyPI version

.. image:: https://travis-ci.org/jasonrbriggs/stomp.py.svg
   :target: https://travis-ci.org/jasonrbriggs/stomp.py
   :alt: Build Status

"stomp.py" is a Python client library for accessing messaging servers (such as ActiveMQ_, Apollo_ or RabbitMQ_) using the STOMP_ protocol (`STOMP v1.0`_, `STOMP v1.1`_ and `STOMP v1.2`_). It can also be run as a standalone, command-line client for testing.

**NOTE:** Stomp.py is officially ending support for Python2.x by Jan 2020. See `python3statement.org`_ for more information. 

.. _STOMP: http://stomp.github.io
.. _`STOMP v1.0`: http://stomp.github.io/stomp-specification-1.0.html
.. _`STOMP v1.1`: http://stomp.github.io/stomp-specification-1.1.html
.. _`STOMP v1.2`: http://stomp.github.io/stomp-specification-1.2.html
.. _`python3statement.org`: http://python3statement.org/

Quick Start
===========

You can connect to a message broker running on the local machine, and send a message using the following example.

.. code:: python

  import stomp

  conn = stomp.Connection()
  conn.set_listener('', MyListener())
  conn.start()
  conn.connect('admin', 'password', wait=True)
  conn.send(body=' '.join(sys.argv[1:]), destination='/queue/test')
  conn.disconnect()

Various documentation and resources include:

- `basic example of using stomp.py`_ with a message listener
- `command-line interface description`_
- installation instructions and downloads on `PyPi stomp.py page`_
- `API documentation`_
- current `test coverage report`_
- `travis continuous integration`_

.. _`basic example of using stomp.py`: https://github.com/jasonrbriggs/stomp.py/wiki/Simple-Example
.. _`command-line interface description`: https://github.com/jasonrbriggs/stomp.py/wiki/Command-Line-Access
.. _`PyPi stomp.py page`: https://pypi.org/project/stomp.py/
.. _`API documentation`: http://jasonrbriggs.github.io/stomp.py/index.html
.. _`test coverage report`: http://jasonrbriggs.github.io/stomp.py/htmlcov/
.. _`travis continuous integration`: https://travis-ci.org/jasonrbriggs/stomp.py


Current version supports:

- Python 2.x and 3.x
- STOMP version 1.0, 1.1 and 1.2

There is also legacy 3.1.7 version using the old 3-series code (see `3.1.7 on PyPi`_ and `3.1.7 on GitHub`_).

.. _`3.1.7 on PyPi`: https://pypi.org/project/stomp.py/3.1.7/
.. _`3.1.7 on GitHub`: https://github.com/jasonrbriggs/stomp.py/tree/stomppy-3series

stomp.py has been perfunctorily tested on:

- ActiveMQ_
- Apollo_
- RabbitMQ_
- stompserver_


.. _ActiveMQ: http://activemq.apache.org/
.. _Apollo: http://activemq.apache.org/apollo/
.. _RabbitMQ: http://www.rabbitmq.com
.. _stompserver: http://stompserver.rubyforge.org

`stomp.py` has been reported to work with JBossMessaging_ in the distant past.

.. _JBossMessaging: http://www.jboss.org/jbossmessaging

For more info on setting up a test server (using virtualbox), contact the developer.

