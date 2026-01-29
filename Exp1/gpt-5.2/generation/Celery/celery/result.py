from __future__ import annotations

import time
from typing import Any, Optional

from .exceptions import TimeoutError


class AsyncResult:
    def __init__(self, id: str, app: Any):
        self.id = id
        self.app = app

    @property
    def backend(self):
        return self.app.executor.backend

    def state(self) -> str:
        return self.backend.get_state(self.id)

    def successful(self) -> bool:
        return self.backend.get_state(self.id) == "SUCCESS"

    def failed(self) -> bool:
        return self.backend.get_state(self.id) == "FAILURE"

    def ready(self) -> bool:
        return self.backend.get_state(self.id) in ("SUCCESS", "FAILURE")

    def get(self, timeout: Optional[float] = None, propagate: bool = True, interval: float = 0.01) -> Any:
        deadline = None if timeout is None else (time.time() + float(timeout))
        while True:
            state = self.backend.get_state(self.id)
            if state == "SUCCESS":
                return self.backend.get_result(self.id)
            if state == "FAILURE":
                exc = self.backend.get_result(self.id)
                if propagate and isinstance(exc, BaseException):
                    raise exc
                return exc
            if deadline is not None and time.time() >= deadline:
                raise TimeoutError(f"Result not ready within {timeout} seconds")
            time.sleep(interval)


class EagerResult(AsyncResult):
    def __init__(self, id: str, result: Any, state: str, app: Any):
        super().__init__(id, app=app)
        self._result = result
        self._state = state

    def state(self) -> str:
        return self._state

    def successful(self) -> bool:
        return self._state == "SUCCESS"

    def failed(self) -> bool:
        return self._state == "FAILURE"

    def ready(self) -> bool:
        return True

    def get(self, timeout: Optional[float] = None, propagate: bool = True, interval: float = 0.0) -> Any:
        if self._state == "FAILURE" and propagate and isinstance(self._result, BaseException):
            raise self._result
        return self._result