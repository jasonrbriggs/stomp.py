import importlib

import pytest

import stomp
from stomp.utils import *


class TestUtils(object):
    def test_returns_true_when_localhost(self):
        assert 1 == is_localhost(("localhost", 8000))
        assert 1 == is_localhost(("127.0.0.1", 8000))
        assert 2 == is_localhost(("192.168.1.92", 8000))

    def test_convert_frame(self):
        f = Frame("SEND", {
            "header1": "value1",
            "headerNone": None,
            " no ": " trimming ",
        }, "this is the body")

        lines = convert_frame(f)

        s = pack(lines)

        assert bytearray("SEND\n no : trimming \nheader1:value1\n\nthis is the body\x00", "ascii") == s

    def test_parse_headers(self):
        lines = [
            r"h1:foo\c\\bar  ",
            r"h1:2nd h1 ignored -- not a must, but allowed and that is how we behave ATM",
            r"h\c2:baz\r\nquux",
            r"h3:\\n\\c",
            r"against-spec:\t",  # should actually raise or something, we're against spec here ATM
            r" foo : bar",
        ]
        assert {
            "h1": r"foo:\bar  ",
            "h:2": "baz\r\nquux",
            "h3": r"\n\c",
            "against-spec": r"\t",
            " foo ": " bar",
        } == parse_headers(lines)

    def test_calculate_heartbeats(self):
        chb = (3000, 5000)
        shb = map(str, reversed(chb))
        assert (3000, 5000) == calculate_heartbeats(shb, chb)
        shb = ("6000", "2000")
        assert (3000, 6000) == calculate_heartbeats(shb, chb)
        shb = ("0", "0")
        assert (0, 0) == calculate_heartbeats(shb, chb)
        shb = ("10000", "0")
        assert (0, 10000) == calculate_heartbeats(shb, chb)
        chb = (0, 0)
        assert (0, 0) == calculate_heartbeats(shb, chb)

    def test_parse_frame(self):
        # oddball/broken
        f = parse_frame(b"FOO")
        assert str(f) == str(Frame("FOO", body=b''))
        # empty body
        f = parse_frame(b"RECEIPT\nreceipt-id:message-12345\n\n")
        assert str(f) == str(Frame("RECEIPT", {"receipt-id": "message-12345"}, b''))
        # no headers
        f = parse_frame(b"ERROR\n\n")
        assert str(f) == str(Frame("ERROR", body=b''))
        # regular, different linefeeds
        for lf in b"\n", b"\r\n":
            f = parse_frame(
                b"MESSAGE" + lf +
                b"content-type:text/plain" + lf +
                lf +
                b"hello world!"
            )
            assert str(f) == str(Frame("MESSAGE", {"content-type": "text/plain"}, b"hello world!"))

    def test_clean_default_headers(self):
        Frame('test').headers["foo"] = "bar"
        assert Frame('test').headers == {}

    def test_join(self):
        str = stomp.utils.join((b'a', b'b', b'c'))
        assert "abc" == str

    def test_decode(self):
        assert decode(None) is None
        assert "test" == decode(b"test")

    def test_encode(self):
        assert b"test" == encode("test")
        assert b"test" == encode(b"test")
        with pytest.raises(TypeError):
            encode(None)

    def test_pack(self):
        assert b"testtest" == pack([b"test", b"test"])

    def test_should_skip_hostname_scan(self):
        os.environ["STOMP_SKIP_HOSTNAME_SCAN"] = "true"
        importlib.reload(stomp.utils)

        assert 2 == len(stomp.utils.LOCALHOST_NAMES)
        assert "localhost" in stomp.utils.LOCALHOST_NAMES
        assert "127.0.0.1" in stomp.utils.LOCALHOST_NAMES

        del os.environ["STOMP_SKIP_HOSTNAME_SCAN"]
        importlib.reload(stomp.utils)

        assert len(stomp.utils.LOCALHOST_NAMES) > 2

    def test_mask_passcodes(self):
        lines = [
            "test line 1",
            "test line with passcode: somepassword",
            "test line 3"
        ]

        lines = stomp.utils.clean_lines(lines)

        assert """['test line 1', 'test line with passcode:********', 'test line 3']""" == lines

    # just for coverage
    def test_get_errno(self):
        class ErrObj(object): pass

        o = ErrObj()
        o.args = ["a"]

        assert "a" == stomp.utils.get_errno(o)