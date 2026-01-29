from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Mapping, Optional

from ..exceptions import CeleryError
from ..local import _set_current_app
from ..result import AsyncResult, EagerResult
from ..utils.collections import AttributeDict
from .task import Task, task_from_callable
from ..backends import get_backend


@dataclass
class _AppConfigDefaults:
    broker_url: Optional[str] = "memory://"
    broker: Optional[str] = None
    result_backend: Optional[str] = "cache+memory://"

    task_always_eager: bool = True
    task_eager_propagates: bool = True

    task_ignore_result: bool = False


class Celery:
    """
    Minimal Celery-like application.

    Supports:
    - task decorator: @app.task(...)
    - tasks registry: app.tasks[name] -> Task
    - send_task(name, ...)
    - eager/in-memory result backend
    """

    def __init__(
        self,
        main: Optional[str] = None,
        broker: Optional[str] = None,
        backend: Optional[str] = None,
        include: Optional[Iterable[str]] = None,
        **kwargs: Any,
    ) -> None:
        self.main = main
        self.include = list(include) if include else []

        defaults = _AppConfigDefaults()
        conf = AttributeDict(defaults.__dict__)
        conf.update(kwargs)

        broker_url = kwargs.get("broker_url", None)
        if broker_url is None:
            broker_url = broker if broker is not None else conf.get("broker_url")
        conf["broker_url"] = broker_url
        conf["broker"] = broker if broker is not None else conf.get("broker")

        result_backend = kwargs.get("result_backend", None)
        if result_backend is None:
            result_backend = backend if backend is not None else conf.get("result_backend")
        conf["result_backend"] = result_backend

        self.conf = conf

        self.tasks: Dict[str, Task] = {}

        self.backend = get_backend(self, self.conf.get("result_backend"))

        _set_current_app(self)

    def __repr__(self) -> str:
        return f"<Celery {self.main or 'app'}:0x{id(self):x}>"

    def _new_task_id(self) -> str:
        return str(uuid.uuid4())

    def task(self, *dargs: Any, **dkwargs: Any):
        """
        Decorator: @app.task or @app.task(name=..., bind=...)

        Supports subset of Celery options used by tests:
        - name: custom task name
        - bind: if True, first arg is Task instance
        - ignore_result: if True, do not store result
        """
        if dargs and callable(dargs[0]) and len(dargs) == 1 and not dkwargs:
            return self._register_task_from_callable(dargs[0])

        def _decorator(func: Callable[..., Any]) -> Task:
            return self._register_task_from_callable(func, **dkwargs)

        return _decorator

    def _register_task_from_callable(self, func: Callable[..., Any], **options: Any) -> Task:
        task = task_from_callable(self, func, **options)
        self.tasks[task.name] = task
        return task

    def send_task(
        self,
        name: str,
        args: Optional[Iterable[Any]] = None,
        kwargs: Optional[Mapping[str, Any]] = None,
        countdown: Optional[float] = None,
        eta: Any = None,
        task_id: Optional[str] = None,
        **options: Any,
    ) -> AsyncResult:
        try:
            task = self.tasks[name]
        except KeyError:
            raise KeyError(name)

        return task.apply_async(args=list(args) if args is not None else None, kwargs=dict(kwargs) if kwargs else None, task_id=task_id, countdown=countdown, eta=eta, **options)

    def AsyncResult(self, task_id: str) -> AsyncResult:
        return AsyncResult(task_id, backend=self.backend, app=self)

    def _execute_task(self, task: Task, task_id: str, args: list, kwargs: dict) -> AsyncResult:
        eager = bool(self.conf.get("task_always_eager"))
        propagate = bool(self.conf.get("task_eager_propagates"))
        if eager:
            try:
                retval = task(*args, **kwargs)
            except Exception as exc:
                if propagate:
                    self.backend.store_result(task_id, exc, state="FAILURE", traceback=None, request={"task": task.name})
                else:
                    self.backend.store_result(task_id, exc, state="FAILURE", traceback=None, request={"task": task.name})
                return EagerResult(task_id, backend=self.backend, app=self)
            else:
                if not task.ignore_result:
                    self.backend.store_result(task_id, retval, state="SUCCESS", traceback=None, request={"task": task.name})
                else:
                    self.backend.store_result(task_id, None, state="SUCCESS", traceback=None, request={"task": task.name})
                return EagerResult(task_id, backend=self.backend, app=self)

        # "Non-eager" not implemented; in this library, memory transport is eager.
        raise CeleryError("Non-eager execution is not supported in this minimal implementation.")


_default_app: Optional[Celery] = None


def _get_default_app() -> Celery:
    global _default_app
    if _default_app is None:
        _default_app = Celery("default", broker_url="memory://", result_backend="cache+memory://")
    return _default_app


def shared_task(*dargs: Any, **dkwargs: Any):
    """
    Minimal shared_task decorator. Registers tasks on the current/default app.

    In real Celery, shared_task is app-agnostic and binds later; for tests we
    register immediately on current_app/default app.
    """
    app = _get_default_app()

    if dargs and callable(dargs[0]) and len(dargs) == 1 and not dkwargs:
        return app.task(dargs[0])

    return app.task(*dargs, **dkwargs)