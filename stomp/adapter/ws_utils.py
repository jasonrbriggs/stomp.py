import enum


class SockJSFrame(bytes, enum.Enum):

    OPEN = b'o'
    CLOSE = b'c'
    ARRAY = b'a'
    HEARTBEAT = b'h'

    def __eq__(self, other):
        if not isinstance(other, bytes):
            return False
        return other.startswith(self)
