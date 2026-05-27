from __future__ import annotations

import json
import logging
import socket
import threading
from queue import Queue
from typing import Any

from .request_queue import QueuedRequest
from .schemas import (
    PROTOCOL_VERSION,
    capabilities_payload,
    make_error,
    make_response,
    validate_request,
)
from .state import RuntimeState, get_state


LOGGER = logging.getLogger(__name__)


def start_server() -> None:
    state = get_state()
    if state.running:
        return

    state.stop_event.clear()
    thread = threading.Thread(target=_listener_loop, name="modell-listener", daemon=True)
    state.listener_thread = thread
    state.running = True
    thread.start()
    state.note_result("Server started")


def stop_server() -> None:
    state = get_state()
    if not state.running:
        return
    state.stop_event.set()
    _poke_listener(state.host, state.port)
    if state.listener_thread and state.listener_thread.is_alive():
        state.listener_thread.join(timeout=1.5)
    state.listener_thread = None
    state.running = False
    state.note_result("Server stopped")


def _poke_listener(host: str, port: int) -> None:
    try:
        with socket.create_connection((host, int(port)), timeout=0.2):
            pass
    except OSError:
        pass


def _listener_loop() -> None:
    state = get_state()
    address = (state.host, int(state.port))

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(address)
    server.listen(12)
    server.settimeout(0.5)

    try:
        while not state.stop_event.is_set():
            try:
                conn, _addr = server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            _handle_connection(conn, state)
    finally:
        try:
            server.close()
        except OSError:
            pass


def _handle_connection(conn: socket.socket, state: RuntimeState) -> None:
    with conn:
        conn.settimeout(3.0)
        try:
            data = conn.makefile("rb").readline()
        except OSError:
            return
        if not data:
            return

        request_id = "unknown"
        protocol_version = PROTOCOL_VERSION
        try:
            payload = json.loads(data.decode("utf-8").rstrip("\n"))
            envelope = validate_request(payload)
            request_id = envelope.request_id
            protocol_version = envelope.protocol_version

            if envelope.protocol_version != PROTOCOL_VERSION:
                response = make_error(
                    request_id=envelope.request_id,
                    code="UNSUPPORTED_PROTOCOL",
                    message=f"Expected protocol {PROTOCOL_VERSION}",
                    details={"got": envelope.protocol_version},
                    protocol_version=PROTOCOL_VERSION,
                )
                _send_json_line(conn, response)
                return

            if envelope.token != state.token:
                response = make_error(
                    request_id=envelope.request_id,
                    code="AUTH_FAILED",
                    message="Invalid token",
                    protocol_version=protocol_version,
                )
                _send_json_line(conn, response)
                return

            if envelope.action == "capabilities":
                response = make_response(
                    request_id=envelope.request_id,
                    ok=True,
                    result=capabilities_payload(),
                    error=None,
                    protocol_version=protocol_version,
                )
                _send_json_line(conn, response)
                return

            reply_queue: Queue[dict[str, Any]] = Queue(maxsize=1)
            queued = QueuedRequest(envelope=envelope, response_queue=reply_queue)
            state.request_queue.put(queued)

            try:
                response = reply_queue.get(timeout=state.process_limit_per_tick * 1.0 + 5.0)
            except Exception:
                response = make_error(
                    request_id=envelope.request_id,
                    code="TIMEOUT",
                    message="Request timed out while waiting for timer processing",
                    protocol_version=protocol_version,
                )
            _send_json_line(conn, response)
        except Exception as exc:
            LOGGER.exception("Failed to process request")
            response = make_error(
                request_id=request_id,
                code="BAD_REQUEST",
                message=str(exc),
                protocol_version=protocol_version,
            )
            _send_json_line(conn, response)


def _send_json_line(conn: socket.socket, payload: dict[str, Any]) -> None:
    raw = json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n"
    conn.sendall(raw.encode("utf-8"))
