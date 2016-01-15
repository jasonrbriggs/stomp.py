"""Errors thrown by stomp.py connections.
"""


class ConnectionClosedException(Exception):
    """
    Raised in the receiver thread when the connection has been closed
    by the server.
    """
    pass


class NotConnectedException(Exception):
    """
    Raised when there is currently no server connection.
    """
    pass


class ConnectFailedException(Exception):
    """
    Raised by Connection.attempt_connection when reconnection attempts
    have exceeded Connection.__reconnect_attempts_max.
    """


class InterruptedException(Exception):
    """
    Raised by receive when data read is interrupted.
    """
