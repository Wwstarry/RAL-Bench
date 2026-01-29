from __future__ import annotations

from typing import Any, Dict


class BaseBackend:
    def store_result(self, task_id: str, result: Any, state: str, exception: Exception | None = None, traceback: str | None = None) -> None:
        raise NotImplementedError

    def get_task_meta(self, task_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    def get_state(self, task_id: str) -> str:
        return self.get_task_meta(task_id).get("status", "PENDING")