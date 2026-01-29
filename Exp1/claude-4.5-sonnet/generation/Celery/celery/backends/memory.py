"""
In-memory result backend
"""

import threading
from typing import Any, Dict, Tuple
from celery.backends.base import BaseBackend


class MemoryBackend(BaseBackend):
    """In-memory result backend for testing"""
    
    def __init__(self):
        self._results: Dict[str, Tuple[str, Any]] = {}
        self._lock = threading.Lock()
    
    def store_result(self, task_id: str, result: Any, state: str):
        """Store task result"""
        with self._lock:
            self._results[task_id] = (state, result)
    
    def get_result(self, task_id: str) -> Tuple[str, Any]:
        """Get task result, returns (state, result)"""
        with self._lock:
            return self._results.get(task_id, ('PENDING', None))
    
    def forget(self, task_id: str):
        """Remove task result"""
        with self._lock:
            self._results.pop(task_id, None)