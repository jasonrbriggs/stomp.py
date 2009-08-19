import sys

from exception import *
from stomp import Connection, ConnectionListener, StatsListener


class StompCLI(ConnectionListener):
    def __init__(self, host='localhost', port=61613, user='', passcode=''):
        self.c = Connection([(host, port)], user, passcode)
        self.c.set_listener('', self)
        self.c.start()

    def __print_async(self, frame_type, headers, body):
        print "\r  \r",
        print frame_type
        for header_key in headers.keys():
            print '%s: %s' % (header_key, headers[header_key])
        print
        print body
        print '> ',
        sys.stdout.flush()

    def on_connecting(self, host_and_port):
        self.c.connect(wait=True)

    def on_disconnected(self):
        print "lost connection"

    def on_message(self, headers, body):
        self.__print_async("MESSAGE", headers, body)

    def on_error(self, headers, body):
        self.__print_async("ERROR", headers, body)

    def on_receipt(self, headers, body):
        self.__print_async("RECEIPT", headers, body)

    def on_connected(self, headers, body):
        print 'connected'
        self.__print_async("CONNECTED", headers, body)

    def ack(self, args):
        '''
        Usage:
            ack <message-id> [transaction-id]

        Required Parameters:
            message-id - the id of the message being acknowledged

        Optional Parameters:
            transaction-id - the acknowledgement should be a part of the named transaction

        Description:
            The command 'ack' is used to acknowledge consumption of a message from a subscription using client
            acknowledgment. When a client has issued a 'subscribe' with the ack flag set to client, any messages
            received from that destination will not be considered to have been consumed (by the server) until
            the message has been acknowledged.
        '''
        if len(args) < 3:
            self.c.ack(message_id=args[1])
        else:
            self.c.ack(message_id=args[1], transaction=args[2])

    def abort(self, args):
        '''
        Usage:
            abort <transaction-id>

        Required Parameters:
            transaction-id - the transaction to abort

        Description:
            Roll back a transaction in progress.
        '''
        self.c.abort(transaction=args[1])

    def begin(self, args):
        '''
        Usage:
            begin

        Description:
            Start a transaction. Transactions in this case apply to sending and acknowledging -
            any messages sent or acknowledged during a transaction will be handled atomically based on the
            transaction.
        '''
        print 'transaction id: %s' % self.c.begin()

    def commit(self, args):
        '''
        Usage:
            commit <transaction-id>

        Required Parameters:
            transaction-id - the transaction to commit

        Description:
            Commit a transaction in progress.
        '''
        if len(args) < 2:
            print 'expecting: commit <transid>'
        else:
            print 'committing %s' % args[1]
            self.c.commit(transaction=args[1])

    def disconnect(self, args):
        '''
        Usage:
            disconnect

        Description:
            Gracefully disconnect from the server.
        '''
        try:
            self.c.disconnect()
        except NotConnectedException:
            pass # ignore if no longer connected

    def send(self, args):
        '''
        Usage:
            send <destination> <message>

        Required Parameters:
            destination - where to send the message
            message - the content to send

        Description:
            Sends a message to a destination in the messaging system.
        '''
        if len(args) < 3:
            print 'expecting: send <destination> <message>'
        else:
            self.c.send(destination=args[1], message=' '.join(args[2:]))
            
    def sendreply(self, args):
        '''
        Usage:
            sendreply <destination> <correlation-id> <message>

        Required Parameters:
            destination - where to send the message
            correlation-id - the correlating identifier to send with the response
            message - the content to send

        Description:
            Sends a reply message to a destination in the messaging system.
        '''
        if len(args) < 4:
            print 'expecting: sendreply <destination> <correlation-id> <message>'
        else:
            self.c.send(destination=args[1], message="%s\n" % ' '.join(args[3:]), headers={'correlation-id': args[2]})
    
    def sendtrans(self, args):
        '''
        Usage:
            sendtrans <destination> <transaction-id> <message>

        Required Parameters:
            destination - where to send the message
            transaction-id - the id of the transaction in which to enlist this message
            message - the content to send

        Description:
            Sends a message to a destination in the message system, using a specified transaction.
        '''
        if len(args) < 3:
            print 'expecting: sendtrans <destination> <transaction-id> <message>'
        else:
            self.c.send(destination=args[1], message="%s\n" % ' '.join(args[3:]), transaction=args[2])

    def subscribe(self, args):
        '''
        Usage:
            subscribe <destination> [ack]

        Required Parameters:
            destination - the name to subscribe to

        Optional Parameters:
            ack - how to handle acknowledgements for a message; either automatically (auto) or manually (client)

        Description:
            Register to listen to a given destination. Like send, the subscribe command requires a destination
            header indicating which destination to subscribe to. The ack parameter is optional, and defaults to
            auto.
        '''
        if len(args) < 2:
            print 'expecting: subscribe <destination> [ack]'
        elif len(args) > 2:
            print 'subscribing to "%s" with acknowledge set to "%s"' % (args[1], args[2])
            self.c.subscribe(destination=args[1], ack=args[2])
        else:
            print 'subscribing to "%s" with auto acknowledge' % args[1]
            self.c.subscribe(destination=args[1], ack='auto')

    def unsubscribe(self, args):
        '''
        Usage:
            unsubscribe <destination>

        Required Parameters:
            destination - the name to unsubscribe from

        Description:
            Remove an existing subscription - so that the client no longer receive messages from that destination.
        '''
        if len(args) < 2:
            print 'expecting: unsubscribe <destination>'
        else:
            print 'unsubscribing from "%s"' % args[1]
            self.c.unsubscribe(destination=args[1])

    def stats(self, args):
        '''
        Usage:
            stats [on|off]
            
        Description:
            Record statistics on messages sent, received, errors, etc. If no argument (on|off) is specified,
            dump the current statistics.
        '''
        if len(args) < 2:
            stats = self.c.get_listener('stats')
            if stats:
                print stats
            else:
                print 'No stats available'
        elif args[1] == 'on':
            self.c.set_listener('stats', StatsListener())
        elif args[1] == 'off':
            self.c.remove_listener('stats')
        else:
            print 'expecting: stats [on|off]'

    def help(self, args):
        '''
        Usage:
            help [command]

        Description:
            Display info on a specified command, or a list of available commands
        '''
        if len(args) == 1:
            print 'Usage: help <command>, where command is one of the following:'
            print '    '
            for f in dir(self):
                if f.startswith('_') or f.startswith('on_') or f == 'c':
                    continue
                else:
                    print '%s ' % f,
            print ''
            return
        elif not hasattr(self, args[1]):
            print 'There is no command "%s"' % args[1]
            return

        func = getattr(self, args[1])
        if hasattr(func, '__doc__') and getattr(func, '__doc__') is not None:
            print func.__doc__
        else:
            print 'There is no help for command "%s"' % args[1]



def main():
    # If the readline module is available, make command input easier
    try:
        import readline
        def stomp_completer(text, state):
            commands = [ 'subscribe', 'unsubscribe',
                         'send',  'ack',
                         'begin', 'abort', 'commit',
                         'connect', 'disconnect'
                       ]
            for command in commands[state:]:
                if command.startswith(text):
                    return "%s " % command
            return None

        readline.parse_and_bind("tab: complete")
        readline.set_completer(stomp_completer)
        readline.set_completer_delims("")
    except ImportError:
        pass # ignore unavailable readline module

    if len(sys.argv) > 5:
        print 'USAGE: stomp.py [host] [port] [user] [passcode]'
        sys.exit(1)

    if len(sys.argv) >= 2:
        host = sys.argv[1]
    else:
        host = "localhost"

    if len(sys.argv) >= 3:
        port = int(sys.argv[2])
    else:
        port = 61613

    if len(sys.argv) >= 5:
        user = sys.argv[3]
        passcode = sys.argv[4]
    else:
        user = None
        passcode = None

    st = StompCLI(host, port, user, passcode)
    try:
        while True:
            line = raw_input("\r> ")
            if not line or line.lstrip().rstrip() == '':
                continue
            line = line.lstrip().rstrip()
            if line.startswith('quit') or line.startswith('disconnect'):
                break
            split = line.split()
            command = split[0]
            if not command.startswith("on_") and hasattr(st, command):
                getattr(st, command)(split)
            else:
                print 'unrecognized command'
    finally:
        st.disconnect(None)



#
# command line testing
#
if __name__ == '__main__':
    main()