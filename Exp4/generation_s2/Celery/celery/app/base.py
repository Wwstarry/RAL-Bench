import threading
import types
from concurrent.futures import ThreadPoolExecutor

from ..backends.memory import MemoryBackend
from ..exceptions import ImproperlyConfigured
from ..result import AsyncResult
from ..states import STARTED, SUCCESS, FAILURE
from ..utils.uuid import uuid4
from .task import Task


class _Conf(dict):
    """
    Minimal configuration object with attribute access.
    """

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as e:
            raise AttributeError(item) from e

    def __setattr__(self, key, value):
        self[key] = value


class Celery:
    """
    Minimal celery.Celery application.

    Supported:
      - app.task decorator for registration
      - app.send_task(name, args, kwargs)
      - broker_url / result_backend basic fields (memory/eager are supported)
      - eager execution and thread-pool async execution
    """

    def __init__(self, main=None, broker=None, backend=None, broker_url=None, result_backend=None, **kwargs):
        self.main = main or "__main__"
        self._tasks = {}
        self.conf = _Conf()

        # configuration defaults similar-ish to Celery
        self.conf.update(
            task_always_eager=False,
            task_eager_propagates=True,
            task_store_eager_result=True,
            result_backend=result_backend or backend or "memory://",
            broker_url=broker_url or broker or "memory://",
            task_ignore_result=False,
        )
        self.conf.update(kwargs)

        self.backend = self._create_backend(self.conf.get("result_backend"))
        # For non-eager async execution, we still run locally using a thread pool.
        self._executor = ThreadPoolExecutor(max_workers=kwargs.get("worker_concurrency", 8))
        self._shutdown_lock = threading.Lock()
        self._closed = False

    def _create_backend(self, url):
        # Support only memory backend for this kata.
        if url in (None, "", "memory://", "cache+memory://"):
            return MemoryBackend(app=self, url=url)
        # Still fallback to memory backend to keep local tests service-free.
        return MemoryBackend(app=self, url=url)

    @property
    def tasks(self):
        return self._tasks

    def task(self, *dargs, **dkwargs):
        """
        Decorator: @app.task(name=..., bind=...)
        """
        def decorator(fun):
            name = dkwargs.get("name") or f"{fun.__module__}.{fun.__name__}"
            bind = bool(dkwargs.get("bind", False))
            base = dkwargs.get("base", Task)

            task_obj = self._create_task_from_fun(fun, name=name, bind=bind, base=base)
            self._tasks[name] = task_obj
            return task_obj

        # supports @app.task without parentheses
        if dargs and callable(dargs[0]) and len(dargs) == 1 and not dkwargs:
            return decorator(dargs[0])
        return decorator

    def _create_task_from_fun(self, fun, name, bind, base=Task):
        app = self

        class FunTask(base):
            abstract = False

            def run(self, *args, **kwargs):
                if bind:
                    return fun(self, *args, **kwargs)
                return fun(*args, **kwargs)

        t = FunTask()
        t.app = app
        t.name = name
        t.__wrapped__ = fun
        t.bind = bind
        # Carry common attributes for nicer compatibility
        t.__name__ = getattr(fun, "__name__", "task")
        t.__doc__ = getattr(fun, "__doc__", None)
        t.__module__ = getattr(fun, "__module__", None)
        return t

    def send_task(self, name, args=None, kwargs=None, **options):
        args = args or ()
        kwargs = kwargs or {}
        task = self._tasks.get(name)
        if task is None:
            raise KeyError(f"Task {name!r} not registered")
        return task.apply_async(args=args, kwargs=kwargs, **options)

    def _apply_task(self, task, args, kwargs, task_id=None, **options):
        if self._closed:
            raise RuntimeError("Celery app is closed")

        task_id = task_id or uuid4()
        ignore_result = options.get("ignore_result", self.conf.get("task_ignore_result", False))
        always_eager = options.get("task_always_eager", self.conf.get("task_always_eager", False))

        # Eager: execute in current thread
        if always_eager:
            try:
                result = task(*args, **kwargs)
            except BaseException as exc:
                if not ignore_result and self.conf.get("task_store_eager_result", True):
                    self.backend.store_result(task_id, None, FAILURE, exception=exc)
                if self.conf.get("task_eager_propagates", True):
                    raise
                if not ignore_result and self.conf.get("task_store_eager_result", True):
                    # store exception object as "result" too, loosely like Celery meta
                    self.backend.store_result(task_id, None, FAILURE, exception=exc)
                return AsyncResult(task_id, backend=self.backend, app=self)
            else:
                if not ignore_result and self.conf.get("task_store_eager_result", True):
                    self.backend.store_result(task_id, result, SUCCESS, exception=None)
                return AsyncResult(task_id, backend=self.backend, app=self)

        # Async: execute in thread pool, store result in backend.
        if not ignore_result:
            self.backend.store_result(task_id, None, STARTED, exception=None)

        def runner():
            try:
                res = task(*args, **kwargs)
            except BaseException as exc:
                if not ignore_result:
                    self.backend.store_result(task_id, None, FAILURE, exception=exc)
                return
            if not ignore_result:
                self.backend.store_result(task_id, res, SUCCESS, exception=None)

        self._executor.submit(runner)
        return AsyncResult(task_id, backend=self.backend, app=self)

    def close(self):
        with self._shutdown_lock:
            if self._closed:
                return
            self._executor.shutdown(wait=True, cancel_futures=False)
            self._closed = True

    # Compatibility stubs (not fully implemented, but often imported)
    def worker_main(self, argv=None):
        raise NotImplementedError("This minimal implementation does not support external worker processes.")

    def start(self, argv=None):
        return self.worker_main(argv=argv)