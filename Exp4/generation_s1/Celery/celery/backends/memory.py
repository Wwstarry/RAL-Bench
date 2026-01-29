from __future__ import annotations

import threading
from typing import Any, Dict

from ..states import PENDING
from .base import BaseBackend


class MemoryBackend(BaseBackend):
    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def store_result(self, task_id: str, result: Any, state: str, exception: Exception | None = None, traceback: str | None = None) -> None:
        meta = {"status": state, "result": result, "exception": exception, "traceback": traceback}
        with self._lock:
            self._data[task_id] = meta

    def get_task_meta(self, task_id: str) -> Dict[str, Any]:
        with self._lock:
            meta = self._data.get(task_id)
            if meta is None:
                return {"status": PENDING, "result": None, "exception": None, "traceback": None}
            return dict(meta)