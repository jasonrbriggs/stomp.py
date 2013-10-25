README
======

"stomp.py" is a Python client library for accessing messaging servers (such as ActiveMQ, Apollo or RabbitMQ) using the [STOMP protocol](http://stomp.github.io) (versions 1.0 and 1.1). It can also be run as a standalone, command-line client for testing.


Quick Start
-----------

A basic example of using stomp.py can be found [here](https://github.com/kwoli/stomp.py/wiki/Simple-Example). Testing via the command-line interface is described [here](https://github.com/kwoli/stomp.py/wiki/Command-Line-Access).

Downloads can be found on [PyPi](https://pypi.python.org/pypi/stomp.py).

Please note that stomp.py was available as a single file (stomp.py), but as of version 2 was split into multiple files in a module directory (click [this link](https://code.google.com/p/stomppy/downloads/detail?name=stomp.py&can=1&q=) if you still want access to this older version).

Select:

- Version 4.0+ for both Python2.x and Python3.x (note this version separates transport from protocol)
- Version 3.0+ for both Python2.x and Python3.x
- Version 2.0.x for Python2.x, or
- Version 2.2+ for Python3.x

stomp.py has been perfunctorily tested on: [ActiveMQ](http://activemq.apache.org/), [Apollo](http://activemq.apache.org/), [RabbitMQ](http://www.rabbitmq.com), [stompserver](http://stompserver.rubyforge.org), and has been reported to work with [JBossMessaging](http://www.jboss.org/jbossmessaging). For more info on setting up the test server (using virtualbox), contact the developer(s).


Contributors
------------

_(If you've contributed code to stomp.py and your name is missing from this list, let me know)_

Julian Scheid ([Rising Sun Pictures](http://open.rsp.com.au/))  
Andreas Schobel  
Fernando Ciciliati  
Eugene Strulyov  
Gavin M. Roy  
Martin Pieuchot  
Joe Gdaniec  
Jayson Vantuyl  
Tatiana Al-Chueyr Martins  


What's In This Release
----------------------

This release contains the following:

README.md	                    - This file  
LICENSE 		                - Software license  
stomp/                          - The stomp.py client library code  
stomp/test/                     - Test code for the library  
stomp/bridge/                   - Bridges for message brokers which don't support STOMP  
stomp/bridge/README-oracle      - Info on the Oracle AQ bridge  

