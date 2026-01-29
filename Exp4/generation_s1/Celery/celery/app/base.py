from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from ..backends import get_backend_by_url
from ..brokers import get_broker_by_url
from ..exceptions import ImproperlyConfigured
from ..utils.uuid import uuid as uuidgen
from .task import Task


class Conf(dict):
    """Dict-like configuration with attribute access."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self[name]
        except KeyError as e:
            raise AttributeError(name) from e


@dataclass
class _AppTaskSpec:
    fun: Callable[..., Any]
    name: str
    bind: bool


class Celery:
    """
    Minimal Celery-like application.

    Supported:
      - app.task decorator with name= and bind=
      - sending tasks by name: app.send_task
      - eager execution mode: conf.task_always_eager
      - in-memory broker and backend: memory://
    """

    def __init__(
        self,
        main: Optional[str] = None,
        broker: Optional[str] = None,
        backend: Optional[str] = None,
        broker_url: Optional[str] = None,
        result_backend: Optional[str] = None,
        include: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> None:
        self.main = main or "__main__"
        self.tasks: Dict[str, Task] = {}

        # Normalize aliases
        broker_url = broker_url or broker or kwargs.get("broker_url") or kwargs.get("broker")
        result_backend = result_backend or backend or kwargs.get("result_backend") or kwargs.get("backend")

        # Defaults
        broker_url = broker_url or "memory://"
        result_backend = result_backend or "memory://"

        self.conf = Conf()
        self.conf.update(
            {
                "broker_url": broker_url,
                "broker": broker_url,
                "result_backend": result_backend,
                "backend": result_backend,
                "task_always_eager": False,
                "task_eager_propagates": True,
                "task_store_eager_result": True,
            }
        )

        # Create backend first (AsyncResult uses it)
        self.backend = get_backend_by_url(self.conf.result_backend)

        # Broker with a dispatch callback
        self.broker = get_broker_by_url(self.conf.broker_url, dispatch=self._dispatch_message)

        # include is ignored; exists for compatibility
        self.include = include or []

    def _task_name_from_fun(self, fun: Callable[..., Any]) -> str:
        mod = getattr(fun, "__module__", None) or "__main__"
        name = getattr(fun, "__name__", None) or fun.__class__.__name__
        return f"{mod}.{name}"

    def register_task(self, task: Task) -> Task:
        if not task.name:
            raise ImproperlyConfigured("Task must have a name before registration")
        task.app = self
        self.tasks[task.name] = task
        return task

    def task(self, *dargs: Any, **dkwargs: Any):
        """
        Decorator to register a function as a task.

        Supports:
          @app.task
          @app.task()
          @app.task(name="x", bind=True)
        """
        name_opt = dkwargs.pop("name", None)
        bind_opt = bool(dkwargs.pop("bind", False))
        if dkwargs:
            # ignore extra options for minimal compatibility
            pass

        def _decorate(fun: Callable[..., Any]) -> Task:
            tname = name_opt or self._task_name_from_fun(fun)
            task_obj = Task(fun=fun, name=tname, app=self, bind=bind_opt)
            self.register_task(task_obj)
            return task_obj

        # If used as @app.task without parentheses
        if dargs and callable(dargs[0]) and len(dargs) == 1 and not name_opt and not bind_opt:
            return _decorate(dargs[0])

        return _decorate

    def send_task(self, name: str, args: Optional[tuple] = None, kwargs: Optional[dict] = None, **options: Any):
        args = tuple(args or ())
        kwargs = dict(kwargs or {})
        try:
            task = self.tasks[name]
        except KeyError as e:
            raise KeyError(f"Unknown task: {name}") from e
        return task.apply_async(args=args, kwargs=kwargs, **options)

    def _dispatch_message(self, message: dict) -> None:
        """
        Called by the broker worker thread to execute a queued task message.
        """
        task_name = message["task"]
        task_id = message["id"]
        args = tuple(message.get("args") or ())
        kwargs = dict(message.get("kwargs") or {})

        task = self.tasks.get(task_name)
        if task is None:
            # If unknown, mark failure so AsyncResult.get() raises
            self.backend.store_result(
                task_id,
                result=None,
                state="FAILURE",
                exception=KeyError(f"Unknown task: {task_name}"),
                traceback=None,
            )
            return

        task._execute(task_id=task_id, args=args, kwargs=kwargs, eager=False)