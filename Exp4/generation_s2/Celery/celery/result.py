import time
import threading

from .exceptions import TimeoutError
from .states import PENDING, SUCCESS, FAILURE


class AsyncResult:
    """
    Minimal AsyncResult.

    Backed by an in-memory backend owned by the Celery app.
    """

    def __init__(self, task_id, backend, app=None):
        self.id = task_id
        self.backend = backend
        self.app = app

    @property
    def state(self):
        meta = self.backend.get_meta(self.id)
        return meta.get("status", PENDING)

    status = state

    def successful(self):
        return self.state == SUCCESS

    def failed(self):
        return self.state == FAILURE

    def ready(self):
        s = self.state
        return s in (SUCCESS, FAILURE)

    def get(self, timeout=None, propagate=True, interval=0.01):
        """
        Wait for and return the task result.

        If task failed and propagate=True, re-raise the stored exception.
        """
        deadline = None if timeout is None else (time.time() + timeout)
        while True:
            meta = self.backend.get_meta(self.id)
            status = meta.get("status", PENDING)
            if status == SUCCESS:
                return meta.get("result")
            if status == FAILURE:
                exc = meta.get("exception")
                if propagate and exc is not None:
                    raise exc
                return meta.get("result")
            if deadline is not None and time.time() >= deadline:
                raise TimeoutError(f"Result {self.id} not ready within {timeout} seconds")
            # allow other threads to run
            time.sleep(interval)

    def __repr__(self):
        return f"<AsyncResult: {self.id} state={self.state}>"