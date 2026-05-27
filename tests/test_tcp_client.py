from __future__ import annotations

import json
from typing import Any

import pytest

from modell.config import BlenderConfig
from modell.tcp_client import ProtocolResponseError, TCPClient


class _FakeReader:
    def __init__(self, line: bytes) -> None:
        self._line = line

    def readline(self) -> bytes:
        return self._line

    def __enter__(self) -> "_FakeReader":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        _ = (exc_type, exc, tb)


class _FakeSocket:
    def __init__(self, response_line: bytes) -> None:
        self.response_line = response_line
        self.sent = b""

    def settimeout(self, _timeout: float) -> None:
        return None

    def sendall(self, data: bytes) -> None:
        self.sent += data

    def makefile(self, _mode: str) -> _FakeReader:
        return _FakeReader(self.response_line)

    def __enter__(self) -> "_FakeSocket":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        _ = (exc_type, exc, tb)


def _client() -> TCPClient:
    return TCPClient(
        BlenderConfig(
            host="127.0.0.1",
            port=8765,
            token="test-token",
            timeout_seconds=1,
            connect_retries=0,
            retry_backoff_seconds=0,
        )
    )


def test_tcp_client_sends_newline_and_token(monkeypatch: pytest.MonkeyPatch) -> None:
    response = {
        "protocol_version": "1.0",
        "request_id": "req-1",
        "ok": True,
        "result": {"message": "pong"},
        "error": None,
    }
    fake_sock = _FakeSocket((json.dumps(response) + "\n").encode("utf-8"))

    def fake_create_connection(_address: tuple[str, int], timeout: float) -> _FakeSocket:
        _ = timeout
        return fake_sock

    monkeypatch.setattr("socket.create_connection", fake_create_connection)

    result = _client().request("ping", {}, request_id="req-1")

    assert result == {"message": "pong"}
    assert fake_sock.sent.endswith(b"\n")
    sent_json = json.loads(fake_sock.sent.decode("utf-8").rstrip("\n"))
    assert sent_json["token"] == "test-token"
    assert sent_json["request_id"] == "req-1"
    assert sent_json["action"] == "ping"


def test_tcp_client_raises_protocol_response_error(monkeypatch: pytest.MonkeyPatch) -> None:
    response = {
        "protocol_version": "1.0",
        "request_id": "req-2",
        "ok": False,
        "result": None,
        "error": {
            "code": "AUTH_FAILED",
            "message": "Invalid token",
            "details": {},
        },
    }
    fake_sock = _FakeSocket((json.dumps(response) + "\n").encode("utf-8"))

    def fake_create_connection(_address: tuple[str, int], timeout: float) -> _FakeSocket:
        _ = timeout
        return fake_sock

    monkeypatch.setattr("socket.create_connection", fake_create_connection)

    with pytest.raises(ProtocolResponseError, match="Invalid token"):
        _client().request("ping", {}, request_id="req-2")
