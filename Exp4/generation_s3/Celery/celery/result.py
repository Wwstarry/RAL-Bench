from __future__ import annotations

import time
from typing import Any, Optional

from .exceptions import TimeoutError


class AsyncResult:
    def __init__(self, id: str, backend, app=None) -> None:
        self.id = id
        self.backend = backend
        self.app = app

    @property
    def status(self) -> str:
        meta = self.backend.get_task_meta(self.id)
        return meta.get("status", "PENDING")

    @property
    def result(self) -> Any:
        meta = self.backend.get_task_meta(self.id)
        return meta.get("result", None)

    @property
    def traceback(self) -> Optional[str]:
        meta = self.backend.get_task_meta(self.id)
        return meta.get("traceback")

    def successful(self) -> bool:
        return self.status == "SUCCESS"

    def failed(self) -> bool:
        return self.status == "FAILURE"

    def ready(self) -> bool:
        return self.status in ("SUCCESS", "FAILURE")

    def get(self, timeout: Optional[float] = None, propagate: bool = True, interval: float = 0.01, **kwargs: Any) -> Any:
        deadline = None if timeout is None else (time.monotonic() + float(timeout))
        while True:
            meta = self.backend.get_task_meta(self.id)
            status = meta.get("status", "PENDING")
            if status == "SUCCESS":
                return meta.get("result", None)
            if status == "FAILURE":
                exc = meta.get("result")
                if propagate and isinstance(exc, BaseException):
                    raise exc
                return exc
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError(f"Result for {self.id} not ready within {timeout} seconds")
            time.sleep(interval)


class EagerResult(AsyncResult):
    """
    In this minimal implementation, eager results are stored in backend
    and behave like AsyncResult. This class mainly exists for API parity.
    """
    pass