from __future__ import annotations

from modell.models import ActionName, CommonResult
from modell.protocol import (
    PROTOCOL_VERSION,
    dumps_message,
    ensure_protocol_version,
    loads_request_line,
    loads_response_line,
    make_error_response,
    make_request,
    make_success_response,
    response_from_result,
)


def test_request_roundtrip_serialization() -> None:
    request = make_request(
        token="test-token",
        action=ActionName.PING,
        params={"x": 1},
        request_id="req-1",
    )

    wire = dumps_message(request)
    parsed = loads_request_line(wire)

    assert parsed.protocol_version == PROTOCOL_VERSION
    assert parsed.request_id == "req-1"
    assert parsed.token == "test-token"
    assert parsed.action == ActionName.PING
    assert parsed.params == {"x": 1}


def test_response_roundtrip_success_and_error() -> None:
    ok = make_success_response(request_id="req-2", result={"message": "pong"})
    ok_wire = dumps_message(ok)
    ok_parsed = loads_response_line(ok_wire)
    assert ok_parsed.ok is True
    assert ok_parsed.error is None
    assert ok_parsed.result == {"message": "pong"}

    err = make_error_response(request_id="req-3", code="BAD", message="bad request")
    err_wire = dumps_message(err)
    err_parsed = loads_response_line(err_wire)
    assert err_parsed.ok is False
    assert err_parsed.error is not None
    assert err_parsed.error.code == "BAD"


def test_response_from_common_result() -> None:
    request = make_request(token="t", action=ActionName.HEALTH, request_id="req-4")
    result = response_from_result(request, CommonResult(message="done", data={"n": 1}))

    assert result.ok is True
    assert result.request_id == "req-4"
    assert result.result == {"message": "done", "data": {"n": 1}}


def test_ensure_protocol_version_rejects_unknown() -> None:
    try:
        ensure_protocol_version("0.9")
    except ValueError as exc:
        assert "Unsupported protocol version" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported protocol version")
