from __future__ import annotations

import traceback as _traceback
from dataclasses import dataclass
from typing import Any, Callable, Optional

from ..result import AsyncResult
from ..states import FAILURE, SUCCESS
from ..utils.uuid import uuid as uuidgen


@dataclass
class _Request:
    id: str
    args: tuple
    kwargs: dict


class Task:
    """
    Minimal Celery-like Task wrapper around a Python callable.
    """

    def __init__(self, fun: Callable[..., Any], name: str, app: Any, bind: bool = False) -> None:
        self.fun = fun
        self.name = name
        self.app = app
        self.bind = bind
        self.request: Optional[_Request] = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if self.bind:
            return self.fun(self, *args, **kwargs)
        return self.fun(*args, **kwargs)

    def delay(self, *args: Any, **kwargs: Any) -> AsyncResult:
        return self.apply_async(args=args, kwargs=kwargs)

    def apply_async(
        self,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
        task_id: Optional[str] = None,
        **options: Any,
    ) -> AsyncResult:
        args = tuple(args or ())
        kwargs = dict(kwargs or {})
        tid = task_id or uuidgen()
        res = AsyncResult(tid, backend=self.app.backend)

        if bool(self.app.conf.get("task_always_eager", False)):
            try:
                self._execute(task_id=tid, args=args, kwargs=kwargs, eager=True)
            except Exception:
                if bool(self.app.conf.get("task_eager_propagates", True)):
                    raise
            return res

        # Broker path (memory worker thread)
        message = {"task": self.name, "id": tid, "args": args, "kwargs": kwargs}
        self.app.broker.publish(message)
        return res

    def _execute(self, task_id: str, args: tuple, kwargs: dict, eager: bool) -> Any:
        # Provide minimal request for bind=True.
        prev_request = self.request
        self.request = _Request(id=task_id, args=args, kwargs=kwargs)
        try:
            result = self(*args, **kwargs)
        except Exception as exc:
            tb = _traceback.format_exc()
            # Always store failure for consistency; in eager mode may be suppressed by config.
            self.app.backend.store_result(task_id, result=None, state=FAILURE, exception=exc, traceback=tb)
            raise
        finally:
            self.request = prev_request

        if (not eager) or bool(self.app.conf.get("task_store_eager_result", True)):
            self.app.backend.store_result(task_id, result=result, state=SUCCESS, exception=None, traceback=None)
        return result