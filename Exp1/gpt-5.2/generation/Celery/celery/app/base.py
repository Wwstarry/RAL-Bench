from __future__ import annotations

import importlib
import inspect
import threading
import uuid
from types import SimpleNamespace
from typing import Any, Callable, Dict, Optional, Sequence, Tuple, Type, Union

from ..exceptions import TimeoutError
from ..result import AsyncResult
from ..utils.collections import AttributeDict
from ..worker.local import LocalExecutor
from .task import Task


def _is_memory_url(url: Optional[str]) -> bool:
    if not url:
        return True
    return url.startswith("memory://") or url == "memory"


class Celery:
    """
    Minimal Celery-like application.

    Supports:
      - task registration: @app.task(...)
      - eager execution via app.conf.task_always_eager
      - in-memory "broker/result backend" for local execution
    """

    def __init__(
        self,
        main: Optional[str] = None,
        broker: Optional[str] = None,
        backend: Optional[str] = None,
        include: Optional[Sequence[str]] = None,
        **kwargs: Any,
    ):
        self.main = main or "__main__"
        self._tasks: Dict[str, Task] = {}

        # Conf surface (AttributeDict like celery)
        self.conf = AttributeDict(
            broker_url=broker or kwargs.get("broker_url") or kwargs.get("broker"),
            result_backend=backend or kwargs.get("result_backend") or kwargs.get("backend"),
            task_always_eager=bool(kwargs.get("task_always_eager", False)),
            task_eager_propagates=bool(kwargs.get("task_eager_propagates", True)),
            task_ignore_result=bool(kwargs.get("task_ignore_result", False)),
            task_store_eager_result=bool(kwargs.get("task_store_eager_result", True)),
            result_extended=bool(kwargs.get("result_extended", False)),
            timezone=kwargs.get("timezone", "UTC"),
            enable_utc=bool(kwargs.get("enable_utc", True)),
            accept_content=kwargs.get("accept_content", ["json"]),
            task_serializer=kwargs.get("task_serializer", "json"),
            result_serializer=kwargs.get("result_serializer", "json"),
        )

        self.executor = LocalExecutor(app=self)

        # Optionally import modules (for side-effect task registration)
        if include:
            for mod in include:
                importlib.import_module(mod)

        # Provide .tasks mapping similar to celery (read-only-ish)
        self.tasks = SimpleNamespace()
        self._sync_tasks_namespace()

    def _sync_tasks_namespace(self) -> None:
        # Expose mapping semantics via attribute access isn't necessary for tests,
        # but celery exposes app.tasks as dict-like. We'll provide both.
        self.tasks = self._tasks

    def task(
        self,
        *dargs: Any,
        **dkwargs: Any,
    ) -> Callable[[Callable[..., Any]], Task]:
        """
        Decorator: @app.task(name=..., bind=..., base=Task)

        If bind=True, first arg passed to function is task instance (self).
        """
        name: Optional[str] = dkwargs.pop("name", None)
        bind: bool = bool(dkwargs.pop("bind", False))
        base: Type[Task] = dkwargs.pop("base", Task)
        ignore_result: Optional[bool] = dkwargs.pop("ignore_result", None)

        # Accept various celery args but ignore them (compat)
        dkwargs.pop("serializer", None)
        dkwargs.pop("rate_limit", None)
        dkwargs.pop("autoretry_for", None)
        dkwargs.pop("retry_kwargs", None)
        dkwargs.pop("retry_backoff", None)
        dkwargs.pop("retry_jitter", None)
        dkwargs.pop("acks_late", None)
        dkwargs.pop("queue", None)

        if dkwargs:
            # Keep permissive: allow unknown kwargs without failing tests.
            pass

        def _decorate(fun: Callable[..., Any]) -> Task:
            tname = name or f"{fun.__module__}.{fun.__name__}"
            task_obj = base(fun=fun, app=self, name=tname, bind=bind)
            if ignore_result is not None:
                task_obj.ignore_result = bool(ignore_result)
            self._tasks[tname] = task_obj
            self._sync_tasks_namespace()
            return task_obj

        # Support bare decorator usage: @app.task
        if dargs and callable(dargs[0]) and len(dargs) == 1 and not dkwargs:
            return _decorate(dargs[0])
        return _decorate

    def register_task(self, task: Task) -> Task:
        self._tasks[task.name] = task
        self._sync_tasks_namespace()
        return task

    def send_task(
        self,
        name: str,
        args: Optional[Sequence[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        **options: Any,
    ) -> AsyncResult:
        task = self._tasks.get(name)
        if task is None:
            raise KeyError(f"Unknown task: {name!r}")
        return task.apply_async(args=args or (), kwargs=kwargs or {}, **options)

    def AsyncResult(self, task_id: str) -> AsyncResult:
        return AsyncResult(task_id, app=self)

    def signature(self, name: str, args: Optional[Sequence[Any]] = None, kwargs: Optional[Dict[str, Any]] = None):
        # Minimal compat: return an object with .delay/.apply_async executing by name.
        app = self

        class _Sig:
            def __init__(self, task_name: str, a: Tuple[Any, ...], k: Dict[str, Any]):
                self.task = task_name
                self.args = a
                self.kwargs = k

            def delay(self, *more_args: Any, **more_kwargs: Any) -> AsyncResult:
                a = self.args + tuple(more_args)
                k = dict(self.kwargs)
                k.update(more_kwargs)
                return app.send_task(self.task, args=a, kwargs=k)

            def apply_async(self, args=None, kwargs=None, **opts):
                a = tuple(args) if args is not None else self.args
                k = dict(kwargs) if kwargs is not None else dict(self.kwargs)
                return app.send_task(self.task, args=a, kwargs=k, **opts)

        return _Sig(name, tuple(args or ()), dict(kwargs or {}))

    @property
    def broker_connection_retry(self) -> bool:
        return False

    def finalize(self, auto: bool = False) -> None:
        # No-op in this minimal implementation
        return

    def now(self):
        import datetime as _dt
        return _dt.datetime.now(_dt.timezone.utc if self.conf.enable_utc else None)

    def __repr__(self) -> str:
        return f"<Celery {self.main}:0x{id(self):x}>"