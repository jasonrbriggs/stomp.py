import socket

def get_socket(host, port, timeout=None):
    return socket.create_connection((host, port), timeout)