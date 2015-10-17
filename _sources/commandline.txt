=========================================
Using the Command-line client application
=========================================

Once stomp.py is installed, access the command-line client as follows::

    stomp -H 127.0.0.1 -P 61613 -U admin -W password
    
Find more info using --help::

    $ stomp --help
    Usage: stomp [options]

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -H HOST, --host=HOST  Hostname or IP to connect to. Defaults to localhost if
                            not specified.
      -P PORT, --port=PORT  Port providing stomp protocol connections. Defaults to
                            61613 if not specified.
      -U USER, --user=USER  Username for the connection
      -W PASSWORD, --password=PASSWORD
                            Password for the connection
      -F FILENAME, --file=FILENAME
                            File containing commands to be executed, instead of
                            prompting from the command prompt.
      -S STOMP, --stomp=STOMP
                            Set the STOMP protocol version.
      -L LISTEN, --listen=LISTEN
                            Listen for messages on a queue/destination
      -V VERBOSE, --verbose=VERBOSE
                            Verbose logging "on" or "off" (if on, full headers
                            from stomp server responses are printed)
      --ssl                 Enable SSL connection
      
And you can also get more help within the application using the help command::

    > help

    Documented commands (type help <topic>):
    ========================================
    EOF    begin   help  rollback  sendfile   stats        ver
    abort  commit  nack  run       sendrec    subscribe    version
    ack    exit    quit  send      sendreply  unsubscribe
    
Some of the differences to the programmatic API are the ability to run a script, and to send files (``run``, ``sendfile``, ``stats``)::

    > help run
    Usage:
    	run <filename>

    Description:
    	Execute commands in a specified file

    > help sendfile
    Usage:
    	sendfile <destination> <filename>

    Required Parameters:
    	destination - where to send the message
    	filename - the file to send

    Description:
    	Sends a file to a destination in the messaging system.
        
    > help stats
    Usage:
    	stats [on|off]

    Description:
    	Record statistics on messages sent, received, errors, etc. If no argument (on|off) is specified,
    	dump the current statistics.
        
Apart from that, the commands are largely inline with what you can do programmatically. Note that you can run it as a normal CLI, as a standalone listener and use it to run a script of commands.
