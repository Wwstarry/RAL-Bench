"""
Celery-like result and AsyncResult implementation.
"""

import threading
import time
import uuid
from . import states

class AsyncResult:
    """
    A minimal Celery-like AsyncResult for retrieving task state/results.
    """

    _store_lock = threading.Lock()
    # In-memory store: {task_id: {'state': <state>, 'result': <value>, 'exc': <exception>, 'tb': <traceback>}}
    _store = {}

    def __init__(self, task_id, store=None):
        self.id = task_id
        if store is not None:
            # For advanced usage, we could override the global store with a custom one,
            # but we'll keep a single store for simplicity.
            self._store = store

    @classmethod
    def store_result(cls, task_id, result, state=states.SUCCESS, exc=None, tb=None):
        with cls._store_lock:
            cls._store[task_id] = {
                "state": state,
                "result": result,
                "exc": exc,
                "tb": tb,
            }

    @property
    def state(self):
        with self._store_lock:
            entry = self._store.get(self.id, None)
            if not entry:
                return states.PENDING
            return entry["state"]

    @property
    def result(self):
        with self._store_lock:
            entry = self._store.get(self.id, None)
            if not entry:
                return None
            return entry["result"]

    def successful(self):
        return self.state == states.SUCCESS

    def failed(self):
        return self.state == states.FAILURE

    def get(self, timeout=None):
        """
        Blocking get; if the result is not ready, it will wait until
        it becomes ready or timeout is reached.
        """
        start_time = time.time()
        while not self.ready():
            if timeout is not None and (time.time() - start_time) > timeout:
                raise TimeoutError("Task result timeout exceeded.")
            time.sleep(0.01)  # Sleep briefly to avoid busy loop
        with self._store_lock:
            entry = self._store.get(self.id, None)
            if entry:
                if entry["exc"]:
                    # Re-raise stored exception
                    raise entry["exc"]
                return entry["result"]
        return None

    def ready(self):
        return self.state in states.READY_STATES or self.state == states.SUCCESS