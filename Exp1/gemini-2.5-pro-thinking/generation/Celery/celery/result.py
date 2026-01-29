import time
from .exceptions import TimeoutError

class AsyncResult:
    """Represents the result of an asynchronous task."""

    def __init__(self, task_id, backend):
        self.id = task_id
        self.backend = backend
        self._state = "PENDING"

    @property
    def state(self):
        """The task's current state ('PENDING', 'SUCCESS', 'FAILURE')."""
        if self._state not in ("SUCCESS", "FAILURE"):
            self._state = self.backend.get_state(self.id)
        return self._state

    def successful(self):
        """Returns True if the task executed successfully."""
        return self.state == "SUCCESS"

    def failed(self):
        """Returns True if the task failed."""
        return self.state == "FAILURE"

    def get(self, timeout=None, interval=0.1):
        """
        Wait for the task to complete and return its result.

        If the task raised an exception, this method will re-raise it.
        """
        start_time = time.time()
        while True:
            if self.state == "SUCCESS":
                return self.backend.get_result(self.id)
            if self.state == "FAILURE":
                result = self.backend.get_result(self.id)
                if isinstance(result, Exception):
                    raise result
                raise Exception(f"Task failed with a non-exception result: {result}")

            if timeout is not None and (time.time() - start_time) >= timeout:
                raise TimeoutError("The operation timed out.")

            time.sleep(interval)

    def forget(self):
        """Instructs the backend to forget the result."""
        self.backend.forget(self.id)