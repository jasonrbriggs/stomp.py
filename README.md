README
======

"stomp.py" is a Python client library for accessing messaging servers (such as ActiveMQ, Apollo or RabbitMQ) using the [STOMP protocol](http://stomp.github.io) (versions [1.0](http://stomp.github.io/stomp-specification-1.0.html), [1.1](http://stomp.github.io/stomp-specification-1.1.html) and [1.2](http://stomp.github.io/stomp-specification-1.2.html)). It can also be run as a standalone, command-line client for testing.


Quick Start
-----------

You can connect to a message broker running on the local machine, and send a message using the following example:

```python
import stomp

conn = stomp.Connection()
conn.set_listener('', MyListener())
conn.start()
conn.connect('admin', 'password', wait=True)
conn.send(body=' '.join(sys.argv[1:]), destination='/queue/test')
conn.disconnect()
```

A basic example of using stomp.py, with a message listener, can be found [here](https://github.com/jasonrbriggs/stomp.py/wiki/Simple-Example). Testing via the command-line interface is described [here](https://github.com/jasonrbriggs/stomp.py/wiki/Command-Line-Access).

Downloads can be found on [PyPi](https://pypi.python.org/pypi/stomp.py).
API documentation can be found [here](http://jasonrbriggs.github.io/stomp.py/index.html). Current test coverage can be found [here](http://jasonrbriggs.github.io/stomp.py/htmlcov/), continuous integration on [Travis](https://travis-ci.org/jasonrbriggs/stomp.py).

[Version 4.0+](https://pypi.python.org/pypi/stomp.py) is for both Python2.x and Python3.x - with support for versions 1.0, 1.1 and 1.2 of the protocol.
Legacy clients using the old 3-series code, can find the download for 3.1.7 [here](https://pypi.python.org/pypi/stomp.py/3.1.7) (github branch [here](https://github.com/jasonrbriggs/stomp.py/tree/stomppy-3series))

stomp.py has been perfunctorily tested on: [ActiveMQ](http://activemq.apache.org/), [Apollo](http://activemq.apache.org/apollo/), [RabbitMQ](http://www.rabbitmq.com), [stompserver](http://stompserver.rubyforge.org), and has been reported to work with [JBossMessaging](http://www.jboss.org/jbossmessaging) in the distant past.
For more info on setting up a test server (using virtualbox), contact the developer.


Project Status
--------------

[![PyPI version](https://badge.fury.io/py/stomp.py.svg)](https://badge.fury.io/py/stomp.py)  
[![Build Status](https://travis-ci.org/jasonrbriggs/stomp.py.svg)](https://travis-ci.org/jasonrbriggs/stomp.py)
