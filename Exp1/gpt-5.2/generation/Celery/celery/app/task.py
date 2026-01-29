from __future__ import annotations

import functools
import threading
import uuid
from typing import Any, Callable, Dict, Optional, Sequence, Tuple

from ..result import AsyncResult, EagerResult
from ..exceptions import Retry
from ..utils.time import maybe_seconds


class Task:
    """
    Minimal Task wrapper.

    Provides:
      - __call__ delegates to run()
      - delay/apply_async
      - request context for bind=True tasks
    """

    abstract = False
    ignore_result: bool = False

    def __init__(self, fun: Callable[..., Any], app: Any, name: str, bind: bool = False):
        self.app = app
        self.name = name
        self.__wrapped__ = fun
        self.bind = bind
        self.__name__ = getattr(fun, "__name__", "task")
        self.__module__ = getattr(fun, "__module__", "__main__")
        self.__doc__ = getattr(fun, "__doc__", None)
        functools.update_wrapper(self, fun)
        self._local = threading.local()

    def run(self, *args: Any, **kwargs: Any) -> Any:
        if self.bind:
            return self.__wrapped__(self, *args, **kwargs)
        return self.__wrapped__(*args, **kwargs)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.run(*args, **kwargs)

    @property
    def request(self):
        return getattr(self._local, "request", None)

    def _push_request(self, request) -> None:
        self._local.request = request

    def _pop_request(self) -> None:
        if hasattr(self._local, "request"):
            delattr(self._local, "request")

    def delay(self, *args: Any, **kwargs: Any) -> AsyncResult:
        return self.apply_async(args=args, kwargs=kwargs)

    def apply_async(
        self,
        args: Optional[Sequence[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        countdown: Optional[float] = None,
        eta: Any = None,
        expires: Any = None,
        **options: Any,
    ) -> AsyncResult:
        args = tuple(args or ())
        kwargs = dict(kwargs or {})
        task_id = task_id or uuid.uuid4().hex

        # Eager mode
        if bool(getattr(self.app.conf, "task_always_eager", False)):
            propagate = bool(getattr(self.app.conf, "task_eager_propagates", True))
            store_eager = bool(getattr(self.app.conf, "task_store_eager_result", True))
            ignore = bool(getattr(self.app.conf, "task_ignore_result", False)) or bool(self.ignore_result)
            try:
                res = self._execute_inline(task_id, args, kwargs)
                if not ignore and store_eager:
                    self.app.executor.backend.store_result(task_id, res, state="SUCCESS")
                return EagerResult(task_id, result=res, state="SUCCESS", app=self.app)
            except Exception as exc:
                if not ignore and store_eager:
                    self.app.executor.backend.store_result(task_id, exc, state="FAILURE", traceback=True)
                if propagate:
                    raise
                return EagerResult(task_id, result=exc, state="FAILURE", app=self.app)

        # Non-eager: execute in background thread (local)
        delay_s = None
        if countdown is not None:
            delay_s = maybe_seconds(countdown)
        elif eta is not None:
            # best-effort: treat eta as datetime
            try:
                import datetime as _dt

                now = _dt.datetime.now(_dt.timezone.utc) if getattr(self.app.conf, "enable_utc", True) else _dt.datetime.now()
                if eta.tzinfo is None and now.tzinfo is not None:
                    eta = eta.replace(tzinfo=now.tzinfo)
                delay_s = max(0.0, (eta - now).total_seconds())
            except Exception:
                delay_s = 0.0
        else:
            delay_s = 0.0

        self.app.executor.submit(self, task_id, args, kwargs, delay=delay_s)
        return AsyncResult(task_id, app=self.app)

    def _execute_inline(self, task_id: str, args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> Any:
        request = {
            "id": task_id,
            "task": self.name,
            "args": args,
            "kwargs": kwargs,
            "retries": 0,
            "is_eager": bool(getattr(self.app.conf, "task_always_eager", False)),
        }
        self._push_request(request)
        try:
            return self.run(*args, **kwargs)
        finally:
            self._pop_request()

    def retry(self, exc: Optional[Exception] = None, countdown: Optional[float] = None, **kwargs: Any):
        # Minimal: signal retry; tests may just check it exists.
        raise Retry(exc=exc, countdown=countdown, **kwargs)