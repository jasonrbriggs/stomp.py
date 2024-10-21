## Version 8.2.0 - Apr 2024

 * New binary_mode param on WS connections (https://github.com/jasonrbriggs/stomp.py/pull/419)
 * Correct WSTransport.receive output (https://github.com/jasonrbriggs/stomp.py/pull/422)
 * Change version from tuple to string, add tuple version function to get back to the old value
 * Docker file updates to fix vulnerabilities
 * Exception handling fix for websocket connections
 * Fix to use the defined timeout during the websocket connection
 * Update exception to report when file doesn't exist (https://github.com/jasonrbriggs/stomp.py/pull/438)


## Version 8.1.2 - Apr 2024 [YANKED]

Yanked because there are more than just bug fixes in this release so the version number was wrong. Replaced with 8.2.0.


## Version 8.1.1 - Apr 2024 [YANKED]

Yanked because there are more than just bug fixes in this release so the version number was wrong. Replaced with 8.2.0.


## Version 8.1.0 - Oct 2022

 * Remove ssl expiration check as per PR: https://github.com/jasonrbriggs/stomp.py/pull/380
 * Change deprecated PROTOCOL_TLS to PROTOCOL_TLS_CLIENT
 * Mock dns responses for testing: https://github.com/jasonrbriggs/stomp.py/pull/383/
 * Support for connection over websocket: https://github.com/jasonrbriggs/stomp.py/pull/395
 * Add default arg for try_setsockopt (https://github.com/jasonrbriggs/stomp.py/issues/391)
 * Updating log levels (https://github.com/jasonrbriggs/stomp.py/pull/401)
 * General tidy up of log messages
 

## Version 8.0.1 - May 2022

 * Change code to use cryptography lib rather than PyOpenSSL (which is not recommended for use any more - discussed here: https://github.com/jasonrbriggs/stomp.py/issues/378)


## Version 8.0.0 - Feb 2022

 * Add support for backwards compatible CONNECT in 1.1 and 1.2 protocols (https://github.com/jasonrbriggs/stomp.py/pull/348)
 * Flip DEFAULT_SSL_VERSION to use ssl.PROTOCOL_TLS rather than ssl.PROTOCOL_TLSv1
 * Check SSL certificate for expiry if PyOpenSSL is installed
 * Remove deprecated constructor params (use_ssl, and other ssl params)
 * Minor cleanup (remove debian packaging config, since it didn't work any more)
 * Add log_to_stdout method to force command line logging to stdout (useful for testing)
 * Various updates for docker testing
 * Add mac keepalive functionality
 * Minor update to daemon attribute (https://github.com/jasonrbriggs/stomp.py/pull/361)
 * Fix issue with heartbeat listener disconnecting the socket (https://github.com/jasonrbriggs/stomp.py/issues/219 - https://github.com/jasonrbriggs/stomp.py/pull/369)


## Version 7.0.0 - Apr 2021

(from v6.1.1):
 * Add host bind port patch (https://github.com/jasonrbriggs/stomp.py/issues/331)
 * Tidy up based on pycharm suggestions
 * Change quotes to be consistent (" rather than ')

(from v6.1.0):
 * Remove traceback logging (https://github.com/jasonrbriggs/stomp.py/pull/290)
 * Add support for \r\n EOL handling (as per [stomp protocol v1.2](http://stomp.github.io/stomp-specification-1.2.html#Augmented_BNF))
 * Remove heartbeat loop sleep (issue https://github.com/jasonrbriggs/stomp.py/issues/297, https://github.com/jasonrbriggs/stomp.py/pull/298)
 * Update version number using the makefile and the poetry version command
 * Add `original_headers` access to the Frame so that you can get the original value of a header even if a listener modifies it (issue: https://github.com/jasonrbriggs/stomp.py/issues/300, PR https://github.com/jasonrbriggs/stomp.py/pull/309)
 * Fix for reconnect failures (https://github.com/jasonrbriggs/stomp.py/pull/295)
 * Fix for double disconnect notifications causing issues with reconnection
 * Add 'verbose' to stomp.logging (and defaulting the value to False). Log lines which dump the stacktrace now use that variable - except for a couple of cases (set stomp.logging.verbose = True to change back to the previous behaviour)
 

## Version 6.1.1 - Apr 2021 [YANKED]

 * Add host bind port patch (https://github.com/jasonrbriggs/stomp.py/issues/331)
 * Tidy up based on pycharm suggestions
 * Change quotes to be consistent (" rather than ')


## Version 6.1.0 - Jul 2020 [YANKED]

 * Remove traceback logging (https://github.com/jasonrbriggs/stomp.py/pull/290)
 * Add support for \r\n EOL handling (as per [stomp protocol v1.2](http://stomp.github.io/stomp-specification-1.2.html#Augmented_BNF))
 * Remove heartbeat loop sleep (issue https://github.com/jasonrbriggs/stomp.py/issues/297, https://github.com/jasonrbriggs/stomp.py/pull/298)
 * Update version number using the makefile and the poetry version command
 * Add `original_headers` access to the Frame so that you can get the original value of a header even if a listener modifies it (issue: https://github.com/jasonrbriggs/stomp.py/issues/300, PR https://github.com/jasonrbriggs/stomp.py/pull/309)
 * Fix for reconnect failures (https://github.com/jasonrbriggs/stomp.py/pull/295)
 * Fix for double disconnect notifications causing issues with reconnection
 * Add 'verbose' to stomp.logging (and defaulting the value to False). Log lines which dump the stacktrace now use that variable - except for a couple of cases (set stomp.logging.verbose = True to change back to the previous behaviour)


## Version 6.0.0 - Feb 2020

 * Update to not allow a null (None) listener when calling set_listener
 * Change get_ssl call in connect to be consistent with transport method
 * Add a sleep to the heartbeat loop
 * Minor change to make quote-use more consistent (replace single with double in most places)
 * Change build to use [Python Poetry](https://python-poetry.org/)
 * Test coverage improvement
 * Threading fix (is_alive) - https://github.com/jasonrbriggs/stomp.py/issues/286

(from v5.0.1):
 * Fix logging simplification code (should not be logging to root appender - https://github.com/jasonrbriggs/stomp.py/issues/275)

(from v5.0.0):
 * Fix for credentials exposure (https://github.com/jasonrbriggs/stomp.py/pull/244)
 * Check for ``STOMP_SKIP_HOSTNAME_SCAN`` environment variable before extending ``LOCALHOST_NAMES``
 * Remove python2 backwards compatibility
 * Update dockerfile for better local testing
 * Fix docker and travis setup, so there are consistent builds both locally and via CI 
 * Drop deprecated start/stop methods from connection (issue https://github.com/jasonrbriggs/stomp.py/issues/257)
 * Fix for missing return in get_ssl (https://github.com/jasonrbriggs/stomp.py/pull/258)
 * Clear heartbeat event after heartbeat loop ends (https://github.com/jasonrbriggs/stomp.py/pull/260)
 * Update listener to move receive/message_received/heartbeat_received vars inside the 'with' blocks (https://github.com/jasonrbriggs/stomp.py/pull/252)
 * Simplify logging calls
 * Tidy up listeners (correct the behaviour of TestListener)
 * Fix problem with double-disconnect notification (ihttps://github.com/jasonrbriggs/stomp.py/issues/245)
 * Add facility for PrintingListener to write to log rather than print statements


## Version 5.0.1 - Jan 2020 [YANKED]

 * Fix logging simplification code (should not be logging to root appender - https://github.com/jasonrbriggs/stomp.py/issues/275)


## Version 5.0.0 - Jan 2020 [YANKED]

 * Fix for credentials exposure (https://github.com/jasonrbriggs/stomp.py/pull/244)
 * Check for ``STOMP_SKIP_HOSTNAME_SCAN`` environment variable before extending ``LOCALHOST_NAMES``
 * Remove python2 backwards compatibility
 * Update dockerfile for better local testing
 * Fix docker and travis setup, so there are consistent builds both locally and via CI 
 * Drop deprecated start/stop methods from connection (issue https://github.com/jasonrbriggs/stomp.py/issues/257)
 * Fix for missing return in get_ssl (https://github.com/jasonrbriggs/stomp.py/pull/258)
 * Clear heartbeat event after heartbeat loop ends (https://github.com/jasonrbriggs/stomp.py/pull/260)
 * Update listener to move receive/message_received/heartbeat_received vars inside the 'with' blocks (https://github.com/jasonrbriggs/stomp.py/pull/252)
 * Simplify logging calls
 * Tidy up listeners (correct the behaviour of TestListener)
 * Fix problem with double-disconnect notification (ihttps://github.com/jasonrbriggs/stomp.py/issues/245)
 * Add facility for PrintingListener to write to log rather than print statements


## Version 4.1.22 - Apr 2019

 * Infinite retry attempts (https://github.com/jasonrbriggs/stomp.py/pull/235)
 * Terminate heartbeat thread on shutdown (https://github.com/jasonrbriggs/stomp.py/pull/234)
 * Remove unused wait_on_receipt parameter (https://github.com/jasonrbriggs/stomp.py/pull/237)
 * Reduce verbosity in logging to not include headers unless debug level is turned on (potential security issue as per: https://github.com/jasonrbriggs/stomp.py/issues/226)
 * Fix for disconnect receipt usage in transport (https://github.com/jasonrbriggs/stomp.py/issues/212)
 * Add __enter__/__exit__ to Connection so it can be used as a context (https://github.com/jasonrbriggs/stomp.py/issues/215)
 * Additional ssl options (https://github.com/jasonrbriggs/stomp.py/pull/221/)


## Version 4.1.21 - July 2018

 * Fix for deadlock issue (https://github.com/jasonrbriggs/stomp.py/issues/197)
 * Fix for encoding issue (https://github.com/jasonrbriggs/stomp.py/issues/195)
 * Fix for reconnect issue (https://github.com/jasonrbriggs/stomp.py/issues/202)


## Version 4.1.20 - Feb 2018

 * Tidy up API (remove need for start/stop methods on the connection)
 * Make updating listeners thread-safe (https://github.com/jasonrbriggs/stomp.py/pull/174)
 * Merge patch from Scott W for configuring grace period for heartbeat timeouts (https://github.com/jasonrbriggs/stomp.py/pull/180)
 * Fix ack/nack in CLI
 * Add missing on_receiver_loop_completed handler to ConnectionListener


## Version 4.1.19

 * Replace custom script with setuptools' entry_point for creating the executable
 * Stop waiting for protocol answers when the connection has been closed
 * Add check for is_connected on transport.stop
 * Change command-line tool to use docopt


## Version 4.1.18 - Sep 2017

 * Strip passcode from log messages


## Version 4.1.17 - Feb 2017

 * Add support for password callback (https://github.com/jasonrbriggs/stomp.py/pull/140)
 * Add disconnect receipt handling for better notification of disconnects
 * Error handling for null frames
 * Stop raising exceptions in the receiver loop, if a connection has been disconnected


## Version 4.1.16 - Jan 2017

 * bug fix for heartbeat timeout (https://github.com/jasonrbriggs/stomp.py/issues/129)
 * handle error with invalid/empty frames


## Version 4.1.15 - Nov 2016

 * Minor change to release wheel
 * Note: rolled forward releases to try to fix issue 132 (https://github.com/jasonrbriggs/stomp.py/issues/132)


## Version 4.1.14 - Nov 2016

 * Minor changes for ssl testing (update: now removed)


## Version 4.1.13 - Oct 2016

 * Minor change to release wheel
 * Add proxy testing to makefile
 * Tidy up method parameters
 * Tidy up documentation
 * Improvement to heartbeat handling


## Version 4.1.12 - Oct 2016

 * Merge patch from Nigel S, improving heartbeat accuracy (https://github.com/jasonrbriggs/stomp.py/pull/95)
 * Merge various patches from Ville S (including):
    * fixing receipt id generation (https://github.com/jasonrbriggs/stomp.py/pull/102)
    * generate disconnect receipt ids (https://github.com/jasonrbriggs/stomp.py/pull/108)
    * don't send unnecessary heartbeats (https://github.com/jasonrbriggs/stomp.py/pull/113)
    * fix misdetection of heartbeats (https://github.com/jasonrbriggs/stomp.py/pull/120)
 * Merge patch from Hugh P, adding SNI support (https://github.com/jasonrbriggs/stomp.py/pull/124)
 * Fix for heartbeat calculation error (https://github.com/jasonrbriggs/stomp.py/pull/125)


## Version 4.1.11 - Apr 2016

 * Minor tidy up (missed from prior release)


## Version 4.1.10 - Apr 2016

 * Bug fix for header escaping (https://github.com/jasonrbriggs/stomp.py/issues/82)
 * Merge patches from Ville S:
     * heartbeats - set received timestamp on receipt and error too (https://github.com/jasonrbriggs/stomp.py/pull/79)
     * test class name fixes (https://github.com/jasonrbriggs/stomp.py/pull/80)
     * support \r\n\r\n preamble end on content-length search (https://github.com/jasonrbriggs/stomp.py/pull/81)
     * on-demand logging message expansion (https://github.com/jasonrbriggs/stomp.py/pull/85)
     * bump connect error logging level to warning (https://github.com/jasonrbriggs/stomp.py/pull/87)
     * assign names to heartbeat and receiver threads (https://github.com/jasonrbriggs/stomp.py/pull/88)
     * remove unused HeartbeatListener.connected (https://github.com/jasonrbriggs/stomp.py/pull/89)
     * support for heartbeats on CLI (https://github.com/jasonrbriggs/stomp.py/pull/100)
 * Merge patch from Mikael V:
     * add header support in CLI (https://github.com/jasonrbriggs/stomp.py/pull/86)
 * Bug fix for on_before_message error (https://github.com/jasonrbriggs/stomp.py/issues/99)


## Version 4.1.9 - Jan 2016

 * Merge patches from Pavel S:
     * support mixed string and bytes as input (https://github.com/jasonrbriggs/stomp.py/pull/66)
     * toggle sending of `content-length` header (https://github.com/jasonrbriggs/stomp.py/pull/67)
 * Minor logging change
 * Various documentation updates
 * Merge code improvement patches from Ville S:
     * use time.monotonic for timekeeping where available (https://github.com/jasonrbriggs/stomp.py/pull/74)
     * define gcd compat only where needed (https://github.com/jasonrbriggs/stomp.py/pull/75)
     * handle locking with "with" (https://github.com/jasonrbriggs/stomp.py/pull/76)
     * misc small improvements (https://github.com/jasonrbriggs/stomp.py/pull/77)
 * Merge patch from nigelsim to improve heartbeat handling for ActiveMQ:
     * heartbeat flexibility to support ActiveMQ (https://github.com/jasonrbriggs/stomp.py/pull/78)


## Version 4.1.8 - Nov 2015

 * Fix missing import (https://github.com/jasonrbriggs/stomp.py/issues/61)
 * Code tidy up


## Version 4.1.7 - Nov 2015

 * Merge patches from Ville S:
    * use constants more (https://github.com/jasonrbriggs/stomp.py/pull/56)
    * do not send headers with None values (https://github.com/jasonrbriggs/stomp.py/pull/57)
 * Update source to tidy up documentation
 * Add sphinx generated documentation
 * Fix keepalive bug (https://github.com/jasonrbriggs/stomp.py/issues/60)


## Version 4.1.6 - Aug 2015

 * Generic exception catch on heartbeat send
 * Fix timeout (https://github.com/jasonrbriggs/stomp.py/issues/55)


## Version 4.1.5 - Aug 2015

 * Remove incorrect \r escaping from 1.1 protocol
 * Merge patch from Ville S:
     * don't ship *.pyc (https://github.com/jasonrbriggs/stomp.py/pull/52)


## Version 4.1.4 - Aug 2015

 * Add --ssl option to command line tool
 * Disable CTRL-C in command line tool (when in interactive mode)
 * Add shutdown message to cli


## Version 4.1.3 - Aug 2015

 * Merge patches from Ville S:
    * auto-send content-length when message body is present (https://github.com/jasonrbriggs/stomp.py/pull/48)
    * unescape header names in addition to values (https://github.com/jasonrbriggs/stomp.py/pull/49)
    * remove unnecessary code (https://github.com/jasonrbriggs/stomp.py/pull/50)


## Version 4.1.2 - Jul 2015

 * Merge patch from Ville S to fix coverage in setup (https://github.com/jasonrbriggs/stomp.py/pull/44)
 * Add Ville's change for None-check in backward3.decode (plus unit tests)


## Version 4.1.1 - Jul 2015

 * Merge patches from Ville S covering invalid module references for colours in the CLI, fixing an attribute error and correctly
   invoking the python exe using sys.executable (https://github.com/jasonrbriggs/stomp.py/pull/41,
   https://github.com/jasonrbriggs/stomp.py/pull/42, https://github.com/jasonrbriggs/stomp.py/pull/43)


## Version 4.1.0 - Jul 2015

 * Merge patch from George G (https://github.com/jasonrbriggs/stomp.py/pull/31) to fix binary message handling. Note that current
   text-only behaviour is still the default (auto_decode=True on the connection), but will be switched to false in a future
   release, before ultimately being removed.
 * Merge code cleanup patches from Ville S (https://github.com/jasonrbriggs/stomp.py/pull/35,
   https://github.com/jasonrbriggs/stomp.py/pull/36)
 * Merge another code cleanup patch from Ville E (https://github.com/jasonrbriggs/stomp.py/pull/37)


## Version 4.0.16 - Apr 2015

 * Catch attribute error in SSL import (https://github.com/jasonrbriggs/stomp.py/issues/30)
 * Set default ssl ## Version to TLSv1


## Version 4.0.15 - Mar 2015

 * Fix for type error in transport logging (https://github.com/jasonrbriggs/stomp.py/issues/29)


## Version 4.0.14 - Mar 2015

 * refactor transport to make providing new transports easier
 * fix bug in listener (https://github.com/jasonrbriggs/stomp.py/issues/26)
 * Merge Andre's logging changes
 * fix for issue #23 (https://github.com/jasonrbriggs/stomp.py/issues/23), stop stomp.py inserting into the path


## Version 4.0.12 - Jun 2014

 * Merge Chaskiel's patch for defaulting receipt headers
 * Fix defaulting for host_and_ports list
 * Fix exception handling in receiver loop
 * Tidy up logging


## Version 4.0.11 - Feb 2014

 * Merge Rafael's patches for specifying ssl settings as a separate method rather than constructor args
   - https://github.com/jasonrbriggs/stomp.py/pull/6
   - https://github.com/jasonrbriggs/stomp.py/pull/10
 * Fix for header escaping (as per https://github.com/jasonrbriggs/stomp.py/issues/9)
 * Move ip/ports for tests into setup.ini


## Version 4.0.10 - Jan 2014

 * Fix package info on setup (missing adapter package causes problems for command line client
    - see https://github.com/jasonrbriggs/stomp.py/issues/7 for more info


## Version 4.0.9 - Jan 2014

 * Fix minor issue with backward uuid func
 * Fixes for error number handling
 * Fix for message listener return values


## Version 4.0.8 - Jan 2014

 * Fix return on get_listener method (https://github.com/jasonrbriggs/stomp.py/issues/4)


## Version 4.0.7 - Jan 2014

 * Fix problem with heartbeat listener (https://github.com/jasonrbriggs/stomp.py/issues/4)
 * Add alternate aliases for the connection classes
 * Add initial ## Version multicast adapter (providing an interface to use the stomp.py API and send messages via multicast)
 	- note: work in progress


## Version 4.0.6 - Dec 2013

 * Fix missing headers in connect func
 * Throw ConnectFailedException when a connection fails in the 1.2 protocol - if wait=True is set


## Version 4.0.5 - Nov 2013

 * Add command-line subscription listener. So you can do:
     > stomp -H localhost -P 61613 -L /queue/test
 * Add verbose option to command-line client (verbose "on" by default, if "off", headers aren't written to stdout)
 * Fix problem with connect wait (should not wait if the connection fails)
 * Throw exception when the connect fails (only if wait=True)
 * Add PrintingListener (useful for debugging)


## Version 4.0.4 - Nov 2013

 * Fix ack/nack function inconsistencies in each protocol ## Version (as per https://github.com/jasonrbriggs/stomp.py/issues/1)


## Version 4.0.3 - Nov 2013

 * Add script for cmd line access (so you can run `stomp -H localhost -P 61613` rather than python $PATH_TO_STOMP/stomp ....)


## Version 4.0.2 - Oct 2013

 * Fix minor error with 1.2 connections. Add basic unit tests for 1.0, and 1.2


## Version 4.0.1 - Oct 2013

 * Remove the 'transform' method/functionality, as this never went into the official spec. Clients who still want this should
   implement themselves, using a listener (see https://github.com/jasonrbriggs/stomp.py/blob/master/stomp/test/misc_test.py for
   an example)
 * Add support for STOMP 1.2 line endings
 * Enforce "host" header on 1.2 connect requests (note: should be enforced on 1.1 connections, but it seems rabbitmq connections
   fail if host is set)


## Version 4.0.0 - Oct 2013

 * Separate protocol from transport mechanism, to improve the ability to support multiple protocol versions. Note: constructor
   args are changing accordingly.
 * Add initial support for STOMP 1.2
 * Moved username and passcode params out of constructor and into the connect method. The basic connection process is therefore now:

     > conn = stomp.Connection([('localhost', 61613)])
     > conn.start()
     > conn.connect('admin', 'password', wait=True)


## Version 3.1.6 - Sep 2013

 * Integrate fix for threading primitives issue (http://code.google.com/p/stomppy/issues/detail?id=53)
 * Add vhost constructor arg
 * Change cli to __main__ (so you can run `python stomp` rather than `python stomp/cli.py`)
 * Integrate interrupt patch (http://code.google.com/p/stomppy/issues/detail?id=48)
 * Change test hosts and ports so that they're provided from the setup.py file


## Version 3.1.5 - Aug 2013

 * Fix for gcd division error (http://code.google.com/p/stomppy/issues/detail?id=44)
 * Fix bytes incompatibility issue in Python 3.3 (http://code.google.com/p/stomppy/issues/detail?id=51)


## Version 3.1.4 - Jul 2012

 * Add receipt header to disconnect frame if not already present on a 1.1 connection


## Version 3.1.3 - May 2012

 * Fix signature on override_threading method
 * Fix for duplicate header handling
 * Minor fix for ## Version var


## Version 3.1.1 - Feb 2012

 * Fix for encoding problems (issue #34) [Jayson Vantuyl]
 * Possible fix for reconnection problems (issue #32)
 * Fix for broken pipe (error not passed to client - issue #33)
 * Various tidying up of the codebase


## Version 3.1.0 (beta 4) - Oct 2011

 * Heartbeat functionality completed
 * General tidy up of unit tests


## Version 3.1.0 (beta 3) - Oct 2011

  * Stop loading logging configuration in module itself (so stomp.py works better as an add-on library)
  * Fix for connection wait (so that it now actually waits)
  * Add initial heartbeat functionality
  * Add Linux TCP-Keepalive functionality, provided by Jayson Vantuyl


## Version 3.1.0 (beta 2) - Sep 2011

  * Various bug fixes in 1.1 code
  * Fixed bug in ssl support
  * Added facility to override threading library
  * Updated unit test code for Apache Apollo


## Version 3.1.0 (beta 1) - Sep 2011

  * Initial support for STOMP Protocol 1.1
  * New ## Version of CLI
  * Added disconnect receipt functionality


## Version 3.0.4 - Sep 2011

  * Added wait-for-receipt functionality
  * Fixed bug in CLI ## Version command
  * SSL protocol patch
  * Added connection timeout
  * Added facility to not send disconnect frame on disconnect (argument to disconnect function)


## Version 3.0.3 - Jan 2011

  * Fixes for python 2.4
  * Added config.dox to distribution


## Version 3.0.2 beta - Jun 2010

  * Fix for localhost connection problem (issue #17)


## Version 3.0.1 beta - Apr 2010

  * Fixes for Oracle AQ bridge for Python3
  * Change to debian style changelog
