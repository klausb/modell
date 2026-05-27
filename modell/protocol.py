from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from pydantic import Field

from modell.models import ActionName, CommonResult, ModellBaseModel, ProtocolErrorDetail, ProtocolParams


PROTOCOL_VERSION = "1.0"


class ProtocolRequest(ModellBaseModel):
    protocol_version: str = PROTOCOL_VERSION
    request_id: str = Field(default_factory=lambda: uuid4().hex)
    token: str
    action: ActionName | str
    params: ProtocolParams = Field(default_factory=dict)


class ProtocolResponse(ModellBaseModel):
    protocol_version: str = PROTOCOL_VERSION
    request_id: str
    ok: bool
    result: dict[str, Any] | list[Any] | str | int | float | bool | None = None
    error: ProtocolErrorDetail | None = None


def new_request_id() -> str:
    return uuid4().hex


def make_request(
    *,
    token: str,
    action: ActionName | str,
    params: ProtocolParams | None = None,
    request_id: str | None = None,
    protocol_version: str = PROTOCOL_VERSION,
) -> ProtocolRequest:
    return ProtocolRequest(
        protocol_version=protocol_version,
        request_id=request_id or new_request_id(),
        token=token,
        action=action,
        params=params or {},
    )


def make_success_response(
    *,
    request_id: str,
    result: Any = None,
    protocol_version: str = PROTOCOL_VERSION,
) -> ProtocolResponse:
    return ProtocolResponse(
        protocol_version=protocol_version,
        request_id=request_id,
        ok=True,
        result=result,
        error=None,
    )


def make_error_response(
    *,
    request_id: str,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    protocol_version: str = PROTOCOL_VERSION,
) -> ProtocolResponse:
    return ProtocolResponse(
        protocol_version=protocol_version,
        request_id=request_id,
        ok=False,
        result=None,
        error=ProtocolErrorDetail(code=code, message=message, details=details or {}),
    )


def dumps_message(message: ModellBaseModel) -> str:
    return message.model_dump_json()


def loads_request_line(line: str) -> ProtocolRequest:
    payload = json.loads(line)
    return ProtocolRequest.model_validate(payload)


def loads_response_line(line: str) -> ProtocolResponse:
    payload = json.loads(line)
    return ProtocolResponse.model_validate(payload)


def ensure_protocol_version(protocol_version: str) -> None:
    if protocol_version != PROTOCOL_VERSION:
        raise ValueError(f"Unsupported protocol version: {protocol_version}")


def response_from_result(request: ProtocolRequest, result: Any) -> ProtocolResponse:
    if isinstance(result, CommonResult):
        result_payload = result.model_dump()
    else:
        result_payload = result
    return make_success_response(request_id=request.request_id, result=result_payload)