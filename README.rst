========
stomp.py
========

.. image:: https://badge.fury.io/py/stomp.py.svg
    :target: https://badge.fury.io/py/stomp.py
    :alt: PyPI version

.. image:: https://travis-ci.org/jasonrbriggs/stomp.py.svg
    :target: https://travis-ci.org/jasonrbriggs/stomp.py
    :alt: Build Status

"stomp.py" is a Python client library for accessing messaging servers (such as ActiveMQ_, Artemis_ or RabbitMQ_) using the STOMP_ protocol (`STOMP v1.0`_, `STOMP v1.1`_ and `STOMP v1.2`_). It can also be run as a standalone, command-line client for testing.

**NOTE:** Stomp.py has officially ended support for Python2.x. See `python3statement.org`_ for more information. 

.. contents:: ``
    :depth: 1

.. _`STOMP`: http://stomp.github.io
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
  conn.connect('admin', 'password', wait=True)
  conn.send(body=' '.join(sys.argv[1:]), destination='/queue/test')
  conn.disconnect()


Documentation and Resources
===========================

Documentation and resources include:

- a basic example of using stomp.py with a message listener (see the `quick start`_)
- `command-line interface description`_
- installation instructions and downloads on `PyPi stomp.py page`_
- `API documentation`_
- current `test coverage report`_
- `travis`_ for continuous integration builds

.. _`quick start`: http://jasonrbriggs.github.io/stomp.py/quickstart.html
.. _`command-line interface description`: http://jasonrbriggs.github.io/stomp.py/commandline.html
.. _`PyPi stomp.py page`: https://pypi.org/project/stomp.py/
.. _`API documentation`: http://jasonrbriggs.github.io/stomp.py/api.html
.. _`test coverage report`: http://jasonrbriggs.github.io/stomp.py/htmlcov/
.. _`travis`: https://travis-ci.org/jasonrbriggs/stomp.py

Current version supports:

- Python 3.x (Python2 support ended as of Jan 2020)
- STOMP version 1.0, 1.1 and 1.2

There is also legacy 3.1.7 version using the old 3-series code (see `3.1.7 on PyPi`_ and `3.1.7 on GitHub`_).

.. _`3.1.7 on PyPi`: https://pypi.org/project/stomp.py/3.1.7/
.. _`3.1.7 on GitHub`: https://github.com/jasonrbriggs/stomp.py/tree/stomppy-3series

stomp.py has been perfunctorily tested on:

- ActiveMQ_
- Artemis_
- RabbitMQ_
- stompserver_

.. _ActiveMQ: http://activemq.apache.org/
.. _Artemis: https://activemq.apache.org/components/artemis/
.. _RabbitMQ: http://www.rabbitmq.com
.. _stompserver: http://stompserver.rubyforge.org

`stomp.py` has been reported to work with JBossMessaging_ in the distant past (note: no idea whether the same is true of the replacement, HornetQ)

.. _JBossMessaging: http://www.jboss.org/jbossmessaging


Local Testing
=============

For testing locally, you'll need to install docker. Once installed:

#. Create the docker image:
        make docker-image
#. Run the container:
        make run-docker
#. Run stomp.py unit tests:
        make test
#. Cleanup the container afterwards if you don't need it any more:
        make remove-docker


Donate
======

If you find this project useful, why not `buy me a coffee`_.

.. _`buy me a coffee`: https://www.paypal.me/jasonrbriggs
