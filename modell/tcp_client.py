from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from typing import Any

from modell.config import BlenderConfig
from modell.models import ActionName, ProtocolErrorDetail, ProtocolParams
from modell.protocol import (
    dumps_message,
    ensure_protocol_version,
    loads_response_line,
    make_request,
)


class TCPClientError(RuntimeError):
    pass


class ProtocolResponseError(TCPClientError):
    def __init__(self, message: str, *, error: ProtocolErrorDetail | None = None) -> None:
        super().__init__(message)
        self.error = error


@dataclass(slots=True)
class TCPClient:
    config: BlenderConfig

    def request(
        self,
        action: ActionName | str,
        params: ProtocolParams | None = None,
        *,
        request_id: str | None = None,
    ) -> Any:
        request = make_request(
            token=self.config.token,
            action=action,
            params=params or {},
            request_id=request_id,
        )

        last_exc: Exception | None = None
        attempts = self.config.connect_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                response = self._send_request_line(dumps_message(request))
                ensure_protocol_version(response.protocol_version)

                if response.request_id != request.request_id:
                    raise TCPClientError(
                        f"Mismatched request_id: expected {request.request_id}, got {response.request_id}"
                    )

                if not response.ok:
                    message = response.error.message if response.error else "Remote action failed"
                    raise ProtocolResponseError(message, error=response.error)

                return response.result
            except ProtocolResponseError:
                raise
            except (socket.timeout, ConnectionError, OSError, TCPClientError) as exc:
                last_exc = exc
                if attempt >= attempts:
                    break
                backoff = self.config.retry_backoff_seconds * (2 ** (attempt - 1))
                if backoff > 0:
                    time.sleep(backoff)

        raise TCPClientError(f"Request failed after {attempts} attempt(s): {last_exc}")

    def ping(self) -> Any:
        return self.request(ActionName.PING, {})

    def health(self) -> Any:
        return self.request(ActionName.HEALTH, {})

    def capabilities(self) -> Any:
        return self.request(ActionName.CAPABILITIES, {})

    def _send_request_line(self, payload: str):
        address = (self.config.host, self.config.port)
        timeout = self.config.timeout_seconds

        with socket.create_connection(address, timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall((payload + "\n").encode("utf-8"))

            with sock.makefile("rb") as file_handle:
                raw_line = file_handle.readline()

            if not raw_line:
                raise TCPClientError("Server closed connection without sending a response")

            line = raw_line.decode("utf-8").rstrip("\n")
            return loads_response_line(line)
