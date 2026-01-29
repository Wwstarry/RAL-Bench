import threading
import time
from typing import Any, Optional

from celery.exceptions import TaskRevokedError, TimeoutError


class AsyncResult:
    """Result handle for asynchronous tasks."""
    
    def __init__(self, id: str, app=None):
        self.id = id
        self.app = app
        self._result = None
        self._state = "PENDING"
        self._exception = None
        self._ready = False
        self._lock = threading.Lock()
        
    def _set_result(self, result: Any):
        """Set successful result."""
        with self._lock:
            self._result = result
            self._state = "SUCCESS"
            self._ready = True
            
    def _set_exception(self, exception: Exception):
        """Set failed result."""
        with self._lock:
            self._exception = exception
            self._state = "FAILURE"
            self._ready = True
            
    def get(self, timeout: Optional[float] = None, propagate: bool = True):
        """Wait for and return result."""
        if self._ready:
            if self._exception and propagate:
                raise self._exception
            return self._result
            
        # Simulate waiting for result
        start = time.time()
        while not self._ready:
            if timeout and (time.time() - start) > timeout:
                raise TimeoutError("The operation timed out.")
            time.sleep(0.01)
            
        if self._exception and propagate:
            raise self._exception
        return self._result
        
    def successful(self) -> bool:
        """Return True if task executed successfully."""
        return self._state == "SUCCESS"
        
    def failed(self) -> bool:
        """Return True if task failed."""
        return self._state == "FAILURE"
        
    def ready(self) -> bool:
        """Return True if task has finished."""
        return self._ready
        
    @property
    def state(self) -> str:
        """Current task state."""
        return self._state
        
    def __repr__(self):
        return f"<AsyncResult: {self.id}>"