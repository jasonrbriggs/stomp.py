=========================================
Using the Command-line client application
=========================================

Once stomp.py is installed, access the command-line client as follows::

    python -m stomp -H localhost -P 61613

As of version 4.0.3, a stomp.py is also installed into the bin dir (at least on unix), so you can also run::

    stomp -H localhost -P 61613

After a successful connection, you can type commands such as::

    subscribe /queue/test
    send /queue/test hello world

If you need to pass a username and password to the client::

    stomp -H localhost -P 61613 -U admin -W password

Run the following to see the list of startup arguments::

    $ stomp --help
    Stomp.py command-line client

    Usage: stomp [options]

    Options:
      --version                    Show the version number and exit
      -h, --help                   Show this help message and exit
      -H <host>, --host=<port>     Hostname or IP address to connect to. [default: localhost]
      -P <port>, --port=<port>     Port providing stomp protocol connections. [default: 61613]
      -U <user>, --user=<user>     Username for the connection
      -W <password>, --password=<password>
                                   Password for the connection
      -F <filename>, --file=<filename>
                                   File containing commands to be executed, instead of
                                   prompting from the command prompt.
      -S <protocol version>, --protocol=<protocol version>
                                   Set the STOMP protocol version (1.0, 1.1, 1.2) [default: 1.1]
      -L <queue>, --listen=<queue> Listen for messages on a queue/destination
      -V, --verbose                Verbose logging "on" or "off" (if on, full headers
                                   from stomp server responses are printed)
      --heartbeats=<heartbeats>    Heartbeats to request when connecting with protocol >=
                                   1.1 (two comma separated integers required) [default: 0,0]
      --ssl                        Enable SSL connection
      --ssl-key-file=<key-file>    ssl key file
      --ssl-cert-file=<cert-file>  ssl cert file
      --ssl-ca-file=<ca-file>      ssl ca certs file

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
