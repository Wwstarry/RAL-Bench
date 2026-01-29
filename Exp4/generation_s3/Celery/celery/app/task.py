from __future__ import annotations

from typing import Any, Callable, Optional

from ..result import AsyncResult


class Task:
    abstract = True

    def __init__(self) -> None:
        self.app = None
        self.name = ""
        self.__module__ = self.__class__.__module__
        self.__name__ = self.__class__.__name__
        self.ignore_result = False
        self._run = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.run(*args, **kwargs)

    def run(self, *args: Any, **kwargs: Any) -> Any:
        if self._run is None:
            raise NotImplementedError("Task.run must be implemented")
        return self._run(*args, **kwargs)

    def delay(self, *args: Any, **kwargs: Any) -> AsyncResult:
        return self.apply_async(args=list(args), kwargs=dict(kwargs))

    def apply_async(
        self,
        args: Optional[list] = None,
        kwargs: Optional[dict] = None,
        task_id: Optional[str] = None,
        countdown: Any = None,
        eta: Any = None,
        **options: Any,
    ) -> AsyncResult:
        args = args or []
        kwargs = kwargs or {}
        if task_id is None:
            task_id = self.app._new_task_id()
        return self.app._execute_task(self, task_id, args, kwargs)

    def apply(self, args: Optional[list] = None, kwargs: Optional[dict] = None, **options: Any) -> AsyncResult:
        return self.apply_async(args=args or [], kwargs=kwargs or {}, **options)


def task_from_callable(app, func: Callable[..., Any], **options: Any) -> Task:
    name = options.get("name")
    bind = bool(options.get("bind", False))

    ignore_result_opt = options.get("ignore_result", None)
    if ignore_result_opt is None:
        ignore_result = bool(app.conf.get("task_ignore_result", False))
    else:
        ignore_result = bool(ignore_result_opt)

    if name is None:
        name = f"{getattr(func, '__module__', '__main__')}.{getattr(func, '__name__', 'task')}"

    task = Task()
    task.abstract = False
    task.app = app
    task.name = name
    task.ignore_result = ignore_result

    task.__module__ = getattr(func, "__module__", task.__module__)
    task.__name__ = getattr(func, "__name__", task.__name__)

    if bind:
        def _bound_run(*args: Any, **kwargs: Any) -> Any:
            return func(task, *args, **kwargs)
        task._run = _bound_run
    else:
        task._run = func

    return task