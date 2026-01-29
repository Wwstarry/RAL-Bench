from __future__ import annotations

from typing import Any, Dict, Optional


class InMemoryBackend:
    def __init__(self, app=None) -> None:
        self.app = app
        self._data: Dict[str, Dict[str, Any]] = {}

    def store_result(self, task_id: str, result: Any, state: str = "SUCCESS", traceback: Optional[str] = None, request: Optional[dict] = None) -> None:
        self._data[task_id] = {
            "task_id": task_id,
            "status": state,
            "result": result,
            "traceback": traceback,
            "request": request or {},
        }

    def get_task_meta(self, task_id: str) -> Dict[str, Any]:
        return self._data.get(task_id, {"task_id": task_id, "status": "PENDING", "result": None, "traceback": None})


def get_backend(app, backend_url: Optional[str]):
    # Accept common celery-ish strings, but always return in-memory.
    # Examples: "cache+memory://", "memory://", None
    return InMemoryBackend(app=app)