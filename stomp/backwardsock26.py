"""
Python2.6 (and greater) specific versions of various networking (ipv6) functions used by stomp.py
"""

import socket

def get_socket(host, port, timeout=None):
    return socket.create_connection((host, port), timeout)