"""
A minimal pure-Python subset of Celery providing just enough behaviour
for the educational / test-suite usage required by the prompt.

The implementation purposefully ONLY targets the parts exercised by the
tests – it is *not* a full featured Celery replacement.
"""
from __future__ import annotations

import threading
import queue
import time
import types
import uuid
from types import SimpleNamespace
from typing import Any, Callable, Dict, Optional, Tuple

__all__ = [
    "Celery",
    "Task",
    "AsyncResult",
    # states (common subset)
    "PENDING",
    "STARTED",
    "SUCCESS",
    "FAILURE",
]

PENDING = "PENDING"
STARTED = "STARTED"
SUCCESS = "SUCCESS"
FAILURE = "FAILURE"

# ---------------------------------------------------------------------------#
# AsyncResult
# ---------------------------------------------------------------------------#


class AsyncResult:
    """
    Very small subset of celery.result.AsyncResult API.

    Only supports:
        .id                – task id / uuid
        .get(timeout=None) – returns result or raises stored exception
        .successful()      – bool
        .failed()          – bool
        .status            – task state str
    """

    __slots__ = ("id", "_result", "_exc", "_status", "_event", "_ready")

    def __init__(
        self,
        task_id: str,
        result: Any = None,
        exception: BaseException | None = None,
        status: str = PENDING,
    ) -> None:
        self.id = task_id
        self._result = result
        self._exc = exception
        self._status = status
        self._event = threading.Event()
        if status in (SUCCESS, FAILURE):
            self._event.set()

    # ------------------------------------------------------------------ #
    # Internals helpers used by the worker / task runtime
    # ------------------------------------------------------------------ #
    def _store_result(
        self,
        result: Any = None,
        exception: BaseException | None = None,
        status: str = SUCCESS,
    ) -> None:
        self._result = result
        self._exc = exception
        self._status = status
        self._event.set()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def get(self, timeout: float | None = None) -> Any:
        """
        Wait (optionally with timeout) and return the task result.
        Re-raises the stored exception on failure.
        """
        if not self._event.wait(timeout):
            raise TimeoutError("Result not ready.")
        if self._status == FAILURE:
            raise self._exc  # pylint: disable=raising-bad-type
        return self._result

    def successful(self) -> bool:
        return self._status == SUCCESS

    def failed(self) -> bool:
        return self._status == FAILURE

    @property
    def status(self) -> str:  # Celery exposes .status attr
        return self._status


# ---------------------------------------------------------------------------#
# Task abstraction
# ---------------------------------------------------------------------------#


class Task:
    """
    Base Task class from which user defined tasks inherit.

    Only a small subset is provided.
    """

    # Overridden by generated subclasses
    name: str = "<unnamed>"

    def __init__(self, app: "Celery") -> None:
        self.app = app
        self.request: SimpleNamespace | None = None

    # ------------------------------------------------------------------ #
    # User code needs to implement .run(), but since our decorator builds
    # Task subclasses automatically, that is taken care of there.
    # ------------------------------------------------------------------ #
    def run(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    # ------------------------------------------------------------------ #
    # Simplified apply/async helpers
    # ------------------------------------------------------------------ #
    def apply_async(
        self,
        args: Tuple[Any, ...] | None = None,
        kwargs: Optional[Dict[str, Any]] = None,
        **options: Any,
    ) -> AsyncResult:
        """
        Submit the task for (immediate) execution.

        Currently honours the following configuration keys:
            - task_always_eager
            - task_eager_propagates
        """
        args = args or ()
        kwargs = kwargs or {}
        task_id = options.get("task_id") or str(uuid.uuid4())  # for tracing

        async_result = AsyncResult(task_id, status=PENDING)

        # Eager execution – run in current thread/process
        always_eager = self.app.conf.task_always_eager
        if always_eager:
            try:
                self.request = SimpleNamespace(id=task_id, args=args, kwargs=kwargs)
                res = self.run(*args, **kwargs)
                async_result._store_result(res, status=SUCCESS)
            except Exception as exc:  # pylint: disable=broad-except
                async_result._store_result(exception=exc, status=FAILURE)
                if self.app.conf.task_eager_propagates:
                    raise
        else:
            # Non-eager mode: put task into in-memory broker queue
            self.app._broker_put(self.name, args, kwargs, async_result)
        return async_result

    def delay(self, *args: Any, **kwargs: Any) -> AsyncResult:
        """
        Shorthand for apply_async with positional / keyword args.
        """
        return self.apply_async(args=args, kwargs=kwargs)

    # enable calling a task object as a normal function
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.run(*args, **kwargs)


# ---------------------------------------------------------------------------#
# Configuration helper
# ---------------------------------------------------------------------------#


class _ConfProxy:
    """
    Lightweight proxy that behaves like the real Celery .conf object.

    Basically wraps a dict but allows attribute and item access.
    """

    def __init__(self, initial: Optional[Dict[str, Any]] = None) -> None:
        self._data: Dict[str, Any] = dict(initial or {})

    # Mapping-like behaviour
    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    # Attribute access sugar
    def __getattr__(self, item: str) -> Any:
        try:
            return self._data[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

    def __setattr__(self, key: str, value: Any) -> None:
        if key == "_data":
            super().__setattr__(key, value)
        else:
            self._data[key] = value

    def update(self, mapping: Dict[str, Any], **kwargs: Any) -> None:
        self._data.update(mapping, **kwargs)


# ---------------------------------------------------------------------------#
# In-memory broker implementation (extremely simplified)
# ---------------------------------------------------------------------------#


class _MemoryBroker:
    """
    Very small imitation of a message broker / worker pool.
    All tasks are kept in memory and executed by a single background thread.
    """

    def __init__(self) -> None:
        self._queues: Dict[str, "queue.Queue[Tuple[Task, Tuple, Dict, AsyncResult]]"] = {}
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._worker_main, daemon=True)
        self._started = False

    # Interfaces used by Celery below
    def put(
        self, task: Task, args: Tuple[Any, ...], kwargs: Dict[str, Any], async_result: AsyncResult
    ) -> None:
        with self._lock:
            q = self._queues.setdefault(task.name, queue.Queue())
            q.put((task, args, kwargs, async_result))
            if not self._started:
                self._worker.start()
                self._started = True

    # Worker loop
    def _worker_main(self) -> None:
        """
        Poll all known queues and execute tasks. Since this is a teaching
        implementation we simply do a simple polling loop.
        """
        while True:
            idle = True
            with self._lock:
                queues = list(self._queues.values())
            for q in queues:
                try:
                    task, args, kwargs, async_result = q.get_nowait()
                except queue.Empty:
                    continue
                idle = False
                threading.Thread(
                    target=self._execute_task, args=(task, args, kwargs, async_result), daemon=True
                ).start()
            if idle:
                # Sleep a little to avoid busy loop when all queues empty
                time.sleep(0.05)

    def _execute_task(
        self, task: Task, args: Tuple[Any, ...], kwargs: Dict[str, Any], async_result: AsyncResult
    ) -> None:
        async_result._status = STARTED
        try:
            task.request = SimpleNamespace(id=async_result.id, args=args, kwargs=kwargs)
            res = task.run(*args, **kwargs)
            async_result._store_result(res, status=SUCCESS)
        except Exception as exc:  # pylint: disable=broad-except
            async_result._store_result(exception=exc, status=FAILURE)


# ---------------------------------------------------------------------------#
# Celery application
# ---------------------------------------------------------------------------#


class Celery:
    """
    Extremely stripped down stand-in for celery.Celery.
    """

    # Registry of *all* apps created (needed by send_task without app)
    _apps: list["Celery"] = []

    def __init__(self, main: str | None = None, broker: str | None = None, backend: str | None = None, **kwargs: Any) -> None:
        """
        Constructor parameters mirror the real Celery signature loosely.
        """
        self.main = main or "__main__"
        init_conf = dict(broker_url=broker or kwargs.pop("broker_url", None))
        init_conf["result_backend"] = backend or kwargs.pop("backend", kwargs.pop("result_backend", None))
        # defaults
        init_conf.setdefault("task_always_eager", True)  # default to eager for tests
        init_conf.setdefault("task_eager_propagates", True)
        self.conf = _ConfProxy(init_conf)
        self.tasks: Dict[str, Task] = {}
        # in-memory broker always available
        self._broker = _MemoryBroker()
        # register app globally
        Celery._apps.append(self)

    # ------------------------------------------------------------------ #
    # Task registration & decorator
    # ------------------------------------------------------------------ #
    def task(self, *dargs: Any, **dkwargs: Any) -> Callable:
        """
        Usage patterns:
            @app.task
            def fn(...): ...

            @app.task(name="my_name", bind=True)
            def fn(self, ...): ...
        """

        def decorator(func: Callable) -> Task:
            name = dkwargs.get("name") or f"{self.main}.{func.__name__}"
            bind = dkwargs.get("bind", False)

            # Dynamically build task subclass
            if bind:

                class _UserTask(Task):
                    pass

                _UserTask.name = name  # type: ignore

                def run(self, *args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
                    return func(self, *args, **kwargs)

                _UserTask.run = run  # type: ignore

            else:

                class _UserTask(Task):
                    pass

                _UserTask.name = name  # type: ignore

                @staticmethod  # type: ignore
                def run(*args: Any, **kwargs: Any) -> Any:
                    return func(*args, **kwargs)

                _UserTask.run = run  # type: ignore

            # Instantiate task (celery keeps a singleton per task)
            task_obj = _UserTask(app=self)

            # Register in app registry
            self.tasks[name] = task_obj

            # Also attach to module globals so that attribute access still yields task object
            setattr(func, "delay", task_obj.delay)
            setattr(func, "apply_async", task_obj.apply_async)
            setattr(func, "task", task_obj)  # some libs inspect .task attribute
            setattr(task_obj, "__wrapped__", func)  # inspect.getsource friendliness

            return task_obj

        # Handle bare decorator @app.task without params
        if dargs and callable(dargs[0]) and not dkwargs:
            return decorator(dargs[0])
        # else return the decorator waiting for the function
        return decorator

    # ------------------------------------------------------------------ #
    # Sending tasks by name
    # ------------------------------------------------------------------ #
    def send_task(
        self,
        name: str,
        args: Optional[Tuple[Any, ...]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        **options: Any,
    ) -> AsyncResult:
        """
        Generic dispatcher similar to celery.Celery.send_task
        """
        args = args or ()
        kwargs = kwargs or {}
        task = self.tasks.get(name)
        if not task:
            # Try other registered apps
            for app in Celery._apps:
                task = app.tasks.get(name)
                if task:
                    break
        if not task:
            raise KeyError(f"Unknown task name '{name}'")
        return task.apply_async(args=args, kwargs=kwargs, **options)

    # ------------------------------------------------------------------ #
    # Internal helper for broker delegation
    # ------------------------------------------------------------------ #
    def _broker_put(
        self, task_name: str | Task, args: Tuple[Any, ...], kwargs: Dict[str, Any], async_result: AsyncResult
    ) -> None:
        if isinstance(task_name, Task):
            task = task_name
        else:
            task = self.tasks[task_name]
        self._broker.put(task, args, kwargs, async_result)

    # convenience: allow `app.worker_main()` maybe for tests – dummy no-op
    def worker_main(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        """
        The real Celery CLI uses this entrypoint – we only need a stub.
        """
        print("This lightweight Celery replacement does not start worker processes.")


# ---------------------------------------------------------------------------#
# Convenience: top level get_current_app
# ---------------------------------------------------------------------------#


def current_app() -> Celery | None:
    """
    Return the latest created application if any.
    """
    return Celery._apps[-1] if Celery._apps else None