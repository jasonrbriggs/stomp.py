========
stomp.py
========

.. image:: https://badge.fury.io/py/stomp.py.svg
    :target: https://badge.fury.io/py/stomp.py
    :alt: PyPI version

.. image:: https://travis-ci.org/jasonrbriggs/stomp.py.svg
    :target: https://travis-ci.org/jasonrbriggs/stomp.py
    :alt: Build Status

"stomp.py" is a Python client library for accessing messaging servers (such as ActiveMQ_, Artemis_ or RabbitMQ_) using the STOMP_ protocol (`STOMP v1.0`_, `STOMP v1.1`_ and `STOMP v1.2`_). It can also be run as a standalone, command-line client for testing.  NOTE: Stomp.py has officially ended support for Python2.x. See `python3statement.org`_ for more information. 

**If you find this project useful, why not** `buy me a coffee`_.

.. contents:: \ 
    :depth: 1


Quick Start
===========

You can connect to a message broker running on the local machine, and send a message using the following example.

.. code-block:: python

  import stomp

  conn = stomp.Connection()
  conn.connect('admin', 'password', wait=True)
  conn.send(body=' '.join(sys.argv[1:]), destination='/queue/test')
  conn.disconnect()


Documentation and Resources
===========================

- `Main documentation`_
- `API documentation`_ (see `stomp.github.io`_ for details on the STOMP protocol itself)
- A basic example of using stomp.py with a message listener can be found in the `quick start`_ section of the main documentation
- Description of the `command-line interface`_
- `Travis`_ for continuous integration builds
- Current `test coverage report`_
- `PyPi stomp.py page`_

The current version of stomp.py supports:

- Python 3.x (Python2 support ended as of Jan 2020)
- STOMP version 1.0, 1.1 and 1.2

There is also legacy 3.1.7 version using the old 3-series code (see `3.1.7 on PyPi`_ and `3.1.7 on GitHub`_). This is no longer supported, but (at least as of 2018) there were still a couple of reports of this version still being used in the wild.


Testing
=======

stomp.py has been perfunctorily tested on:

- Pivotal `RabbitMQ`_   (`rabbitmq_test.py <https://github.com/jasonrbriggs/stomp.py/blob/dev/stomp/test/rabbitmq_test.py>`_)
- Apache `ActiveMQ`_   (`activemq_test.py <https://github.com/jasonrbriggs/stomp.py/blob/dev/stomp/test/activemq_test.py>`_)
- Apache ActiveMQ `Artemis`_  (`artemis_test.py <https://github.com/jasonrbriggs/stomp.py/blob/dev/stomp/test/artemis_test.py>`_)
- `stompserver`_  (`stompserver_test.py <https://github.com/jasonrbriggs/stomp.py/blob/dev/stomp/test/stompserver_test.py>`_)

For testing locally, you'll need to install docker. Once installed:

#. Create the docker image:
        make docker-image
#. Run the container:
        make run-docker
#. Run stomp.py unit tests:
        make test
#. Cleanup the container afterwards if you don't need it any more:
        make remove-docker


.. _`STOMP`: http://stomp.github.io
.. _`STOMP v1.0`: http://stomp.github.io/stomp-specification-1.0.html
.. _`STOMP v1.1`: http://stomp.github.io/stomp-specification-1.1.html
.. _`STOMP v1.2`: http://stomp.github.io/stomp-specification-1.2.html
.. _`python3statement.org`: http://python3statement.org/

.. _`Main documentation`: http://jasonrbriggs.github.io/stomp.py/index.html
.. _`stomp.github.io`: http://stomp.github.io/
.. _`quick start`: http://jasonrbriggs.github.io/stomp.py/quickstart.html
.. _`command-line interface`: http://jasonrbriggs.github.io/stomp.py/commandline.html
.. _`PyPi stomp.py page`: https://pypi.org/project/stomp.py/
.. _`API documentation`: http://jasonrbriggs.github.io/stomp.py/api.html
.. _`test coverage report`: http://jasonrbriggs.github.io/stomp.py/htmlcov/
.. _`Travis`: https://travis-ci.org/jasonrbriggs/stomp.py

.. _`3.1.7 on PyPi`: https://pypi.org/project/stomp.py/3.1.7/
.. _`3.1.7 on GitHub`: https://github.com/jasonrbriggs/stomp.py/tree/stomppy-3series

.. _`ActiveMQ`:  http://activemq.apache.org/
.. _`Artemis`: https://activemq.apache.org/components/artemis/
.. _`RabbitMQ`: http://www.rabbitmq.com
.. _`stompserver`: http://stompserver.rubyforge.org

.. _`buy me a coffee`: https://www.paypal.me/jasonrbriggs
