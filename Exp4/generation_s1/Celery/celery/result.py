from __future__ import annotations

import time
from typing import Any, Optional

from .exceptions import TimeoutError
from .states import FAILURE, PENDING, SUCCESS


class AsyncResult:
    def __init__(self, id: str, backend: Any) -> None:
        self.id = id
        self.backend = backend

    @property
    def state(self) -> str:
        return self.backend.get_state(self.id)

    @property
    def status(self) -> str:
        return self.state

    def ready(self) -> bool:
        return self.state in (SUCCESS, FAILURE)

    def successful(self) -> bool:
        return self.state == SUCCESS

    def failed(self) -> bool:
        return self.state == FAILURE

    def get(self, timeout: Optional[float] = None, propagate: bool = True, interval: float = 0.01) -> Any:
        deadline = None if timeout is None else (time.monotonic() + float(timeout))
        while True:
            meta = self.backend.get_task_meta(self.id)
            status = meta.get("status", PENDING)
            if status in (SUCCESS, FAILURE):
                if status == SUCCESS:
                    return meta.get("result")
                exc = meta.get("exception")
                if propagate and exc is not None:
                    raise exc
                return exc
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError(f"Result for {self.id} not ready within {timeout}s")
            time.sleep(interval)