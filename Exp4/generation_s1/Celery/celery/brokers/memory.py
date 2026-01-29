from __future__ import annotations

import queue
import threading
from typing import Callable, Optional

from .base import BaseBroker


class MemoryBroker(BaseBroker):
    """
    In-memory broker with a single background worker thread.
    """

    def __init__(self, dispatch: Optional[Callable[[dict], None]] = None) -> None:
        super().__init__(dispatch=dispatch)
        self._q: queue.Queue[dict] = queue.Queue()
        self._worker = threading.Thread(target=self._run, name="celery-memory-broker", daemon=True)
        self._worker.start()

    def publish(self, message: dict) -> None:
        self._q.put(message)

    def _run(self) -> None:
        while True:
            msg = self._q.get()
            try:
                if self.dispatch is not None:
                    self.dispatch(msg)
            finally:
                self._q.task_done()