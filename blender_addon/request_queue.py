from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Queue
from typing import Any

from .schemas import RequestEnvelope


@dataclass(slots=True)
class QueuedRequest:
    envelope: RequestEnvelope
    response_queue: Queue[dict[str, Any]]


class RequestQueue:
    def __init__(self) -> None:
        self._queue: Queue[QueuedRequest] = Queue(maxsize=1024)

    def put(self, item: QueuedRequest) -> None:
        self._queue.put_nowait(item)

    def get_nowait(self) -> QueuedRequest:
        return self._queue.get_nowait()

    def qsize(self) -> int:
        return self._queue.qsize()

    def task_done(self) -> None:
        self._queue.task_done()

    def drain(self) -> list[QueuedRequest]:
        items: list[QueuedRequest] = []
        while True:
            try:
                items.append(self.get_nowait())
            except Empty:
                break
        return items
