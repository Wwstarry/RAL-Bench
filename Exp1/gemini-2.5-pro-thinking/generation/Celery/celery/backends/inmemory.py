import threading
from .base import BaseBackend

class InMemoryBackend(BaseBackend):
    """A result backend that stores results in memory."""

    def __init__(self, url=None, *args, **kwargs):
        self._results = {}
        self._lock = threading.Lock()

    def store_result(self, task_id, result, state, traceback=None):
        """Store a task result in the in-memory dictionary."""
        with self._lock:
            self._results[task_id] = {
                "state": state,
                "result": result,
                "traceback": traceback,
            }

    def _get_task_meta(self, task_id):
        """Retrieve the metadata for a task."""
        with self._lock:
            return self._results.get(task_id)

    def get_result(self, task_id):
        """Get the return value of a successful task."""
        meta = self._get_task_meta(task_id)
        return meta.get("result") if meta else None

    def get_state(self, task_id):
        """Get the current state of a task."""
        meta = self._get_task_meta(task_id)
        return meta.get("state") if meta else "PENDING"

    def forget(self, task_id):
        """Remove a task result from memory."""
        with self._lock:
            self._results.pop(task_id, None)