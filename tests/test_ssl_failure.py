import importlib

import pytest

class TestSSLFailure(object):
    @pytest.mark.run(order=-1)
    def test_ssl_failure(self, monkeypatch):
        import ssl
        monkeypatch.delattr(ssl, "PROTOCOL_TLSv1", raising=True)
        import stomp.transport as t
        importlib.reload(t)
        assert t.DEFAULT_SSL_VERSION is None
        monkeypatch.undo()
        importlib.reload(ssl)

    @pytest.mark.run(order=-1)
    def test_socket_failure(self, monkeypatch):
        import socket
        monkeypatch.delattr(socket, "SO_KEEPALIVE", raising=True)
        import stomp.transport as t
        importlib.reload(t)
        assert t.LINUX_KEEPALIVE_AVAIL == False
        monkeypatch.undo()
        importlib.reload(socket)