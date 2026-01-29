from typing import Any, Dict, Tuple
from celery.backends.base import BaseBackend


class MemoryBackend(BaseBackend):
    def __init__(self):
        self._results: Dict[str, Tuple[str, Any]] = {}
    
    def set_result(self, task_id: str, result: Any, state: str) -> None:
        self._results[task_id] = (state, result)
    
    def get_result(self, task_id: str) -> Tuple[str, Any]:
        if task_id not in self._results:
            return ("PENDING", None)
        return self._results[task_id]