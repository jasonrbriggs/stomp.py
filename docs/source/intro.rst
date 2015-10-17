========================
Introduction to Stomp.py
========================

About Stomp.py
--------------

Stomp.py started as an `"itch-scratching" project <https://en.wikipedia.org/wiki/The_Cathedral_and_the_Bazaar#Lessons_for_creating_good_open_source_software>`_, after discovering that the message broker we were using for inter-application communications in a telecommunications platform, had a text-based protocol called `STOMP <https://stomp.github.io/>`_ you could use for access. We wanted something which could randomly send a variation of messages, easily scriptable - and there was only one other Python-based client library available at the time (which didn't work, and it looked as if the project had stalled). So after a number of evenings spent coding (ah! those were the days - when one could get away with endless coding in the evenings), the first version of stomp.py was created (supporting the basics of the 1.0 protocol, a smidgen of a CLI, and little else). In the 8 or 9 years since its inception, support for the subsequent versions of STOMP have been added, and the command line client has been significantly enhanced.

* Stomp.py currently supports all versions of the stomp protocol (1.0, 1.1 and 1.2)
* Both Python 2 and Python 3 are supported
* The command-line client is installed via pip and has a number of useful features for testing
* The code is perfunctorily tested on: ActiveMQ, RabbitMQ, stompserver, and has been reported to work with JBossMessaging in the distant past. Full test suite runs against Apache Apollo (for info on setting up VirtualBox for testing, contact the developer).


Getting Help
------------

View outstanding issues on the GitHub `issues list <https://github.com/jasonrbriggs/stomp.py/issues>`_, or raise a request for help (note that stomp.py is 'intermittently' supported at times).


Contributors
------------

Julian Scheid (`Rising Sun Pictures <http://open.rsp.com.au/>`_)

Andreas Schobel

Fernando Ciciliati

Eugene Strulyov

Gavin M. Roy

Martin Pieuchot

Joe Gdaniec

Jayson Vantuyl

Tatiana Al-Chueyr Martins

Rafael Durán Casteñada

Chaskiel Grundman

Ville Skyttä