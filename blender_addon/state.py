from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .request_queue import RequestQueue


@dataclass(slots=True)
class RuntimeState:
    running: bool = False
    listener_thread: threading.Thread | None = None
    stop_event: threading.Event = field(default_factory=threading.Event)
    request_queue: RequestQueue = field(default_factory=RequestQueue)
    host: str = "127.0.0.1"
    port: int = 8765
    token: str = "change-me"
    last_request_id: str = ""
    last_action: str = ""
    recent_results: deque[str] = field(default_factory=lambda: deque(maxlen=8))
    process_limit_per_tick: int = 8

    def note_result(self, summary: str) -> None:
        self.recent_results.appendleft(summary)


_STATE = RuntimeState()


def get_state() -> RuntimeState:
    return _STATE


def sync_from_preferences(prefs: Any) -> None:
    state = get_state()
    state.host = prefs.host
    state.port = int(prefs.port)
    state.token = prefs.token
