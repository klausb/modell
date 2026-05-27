from __future__ import annotations

import logging
from queue import Empty

from .actions import ACTION_HANDLERS
from .schemas import capabilities_payload, make_error, make_response
from .state import get_state


LOGGER = logging.getLogger(__name__)
TIMER_INTERVAL_SECONDS = 0.1


def ensure_timer_registered() -> None:
    import bpy

    if not bpy.app.timers.is_registered(process_request_queue):
        bpy.app.timers.register(process_request_queue, first_interval=TIMER_INTERVAL_SECONDS, persistent=True)


def ensure_timer_unregistered() -> None:
    import bpy

    if bpy.app.timers.is_registered(process_request_queue):
        bpy.app.timers.unregister(process_request_queue)


def process_request_queue() -> float:
    state = get_state()
    if not state.running:
        return TIMER_INTERVAL_SECONDS

    processed = 0
    while processed < state.process_limit_per_tick:
        try:
            queued = state.request_queue.get_nowait()
        except Empty:
            break

        envelope = queued.envelope
        state.last_request_id = envelope.request_id
        state.last_action = envelope.action

        try:
            if envelope.action == "capabilities":
                result = capabilities_payload()
            else:
                handler = ACTION_HANDLERS.get(envelope.action)
                if handler is None:
                    raise ValueError(f"No handler for action: {envelope.action}")
                result = handler(envelope.params)
            response = make_response(
                request_id=envelope.request_id,
                ok=True,
                result=result,
                error=None,
                protocol_version=envelope.protocol_version,
            )
            state.note_result(f"ok:{envelope.action}")
        except Exception as exc:
            LOGGER.exception("Action failed: %s", envelope.action)
            response = make_error(
                request_id=envelope.request_id,
                code="ACTION_FAILED",
                message=str(exc),
                protocol_version=envelope.protocol_version,
            )
            state.note_result(f"error:{envelope.action}:{exc}")

        try:
            queued.response_queue.put_nowait(response)
        except Exception:
            pass

        state.request_queue.task_done()
        processed += 1

    return TIMER_INTERVAL_SECONDS
