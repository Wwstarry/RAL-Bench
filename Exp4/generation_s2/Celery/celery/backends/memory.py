import threading

from .base import BaseBackend
from ..states import PENDING


class MemoryBackend(BaseBackend):
    """
    Thread-safe in-memory backend.

    Stores:
      {task_id: {"status": ..., "result": ..., "exception": ...}}
    """

    def __init__(self, app=None, url=None):
        super().__init__(app=app, url=url)
        self._data = {}
        self._lock = threading.RLock()

    def store_result(self, task_id, result, status, exception=None):
        with self._lock:
            self._data[task_id] = {
                "status": status,
                "result": result,
                "exception": exception,
            }

    def get_meta(self, task_id):
        with self._lock:
            return dict(self._data.get(task_id, {"status": PENDING, "result": None}))