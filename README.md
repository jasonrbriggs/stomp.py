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
Various documentation and resources include:
- [basic example of using stomp.py with a message listener](https://github.com/jasonrbriggs/stomp.py/wiki/Simple-Example)
- [command-line interface description](https://github.com/jasonrbriggs/stomp.py/wiki/Command-Line-Access)
- [installation instructions and downloads on PyPi](https://pypi.org/project/stomp.py/)
- [API documentation](http://jasonrbriggs.github.io/stomp.py/index.html)
- [current test coverage report](http://jasonrbriggs.github.io/stomp.py/htmlcov/)
- [travis continuous integration](https://travis-ci.org/jasonrbriggs/stomp.py)

[Current version](https://pypi.org/project/stomp.py/) supports:
- Python 2.x and 3.x
- STOMP version 1.0, 1.1 and 1.2

There is also legacy 3.1.7 version is using the old 3-series code ([PyPi](https://pypi.org/project/stomp.py/3.1.7/), [sources in github branch](https://github.com/jasonrbriggs/stomp.py/tree/stomppy-3series)).

stomp.py has been perfunctorily tested on:
- [ActiveMQ](http://activemq.apache.org/)
- [Apollo](http://activemq.apache.org/apollo/)
- [RabbitMQ](http://www.rabbitmq.com)
- [stompserver](http://stompserver.rubyforge.org)

stomp.py has been reported to work with [JBossMessaging](http://www.jboss.org/jbossmessaging) in the distant past.

For more info on setting up a test server (using virtualbox), contact the developer.


Project Status
--------------

[![PyPI version](https://badge.fury.io/py/stomp.py.svg)](https://badge.fury.io/py/stomp.py)  
[![Build Status](https://travis-ci.org/jasonrbriggs/stomp.py.svg)](https://travis-ci.org/jasonrbriggs/stomp.py)
