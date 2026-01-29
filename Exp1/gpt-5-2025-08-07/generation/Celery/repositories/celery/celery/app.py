import threading
import time
import uuid
from types import SimpleNamespace


PENDING = "PENDING"
STARTED = "STARTED"
SUCCESS = "SUCCESS"
FAILURE = "FAILURE"


def uuid4():
    return str(uuid.uuid4())


class Configuration:
    """
    Minimal configuration surface compatible with Celery tests.

    Attributes exposed:
      - broker_url / broker
      - result_backend / backend
      - task_always_eager
      - task_eager_propagates
    """
    def __init__(self, initial=None):
        data = dict(initial or {})
        # Set defaults if not provided
        data.setdefault("broker_url", data.get("broker"))
        data.setdefault("result_backend", data.get("backend"))
        # Default to in-memory broker/backend and eager execution to be self-contained.
        if data.get("broker_url") is None:
            data["broker_url"] = "memory://"
        if data.get("result_backend") is None:
            data["result_backend"] = "memory://"
        data.setdefault("task_always_eager", True)
        data.setdefault("task_eager_propagates", False)
        self._data = data

    def update(self, mapping=None, **kwargs):
        if mapping:
            self._data.update(mapping)
        if kwargs:
            self._data.update(kwargs)

    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name == "_data":
            return super().__setattr__(name, value)
        self._data[name] = value

    def __repr__(self):
        return f"<Configuration {self._data!r}>"


class InMemoryBackend:
    """
    Very simple in-memory result backend with blocking get semantics.
    Stores task state/result/exception by task_id.
    """
    def __init__(self):
        self._store = {}
        self._events = {}
        self._lock = threading.RLock()

    def store_pending(self, task_id):
        with self._lock:
            if task_id not in self._events:
                self._events[task_id] = threading.Event()
            self._store[task_id] = {"status": PENDING, "result": None, "exception": None, "traceback": None}

    def store_started(self, task_id):
        with self._lock:
            if task_id not in self._events:
                self._events[task_id] = threading.Event()
            meta = self._store.get(task_id, {})
            meta.update({"status": STARTED})
            self._store[task_id] = meta

    def store_result(self, task_id, result, status=SUCCESS):
        with self._lock:
            event = self._events.get(task_id)
            self._store[task_id] = {"status": status, "result": result, "exception": None, "traceback": None}
            if event:
                event.set()
            else:
                self._events[task_id] = threading.Event()
                self._events[task_id].set()

    def store_exception(self, task_id, exc, traceback=None):
        with self._lock:
            event = self._events.get(task_id)
            self._store[task_id] = {"status": FAILURE, "result": None, "exception": exc, "traceback": traceback}
            if event:
                event.set()
            else:
                self._events[task_id] = threading.Event()
                self._events[task_id].set()

    def get_task_meta(self, task_id):
        with self._lock:
            meta = self._store.get(task_id)
            if meta is None:
                return {"status": PENDING, "result": None, "exception": None, "traceback": None}
            return dict(meta)

    def wait_for(self, task_id, timeout=None):
        with self._lock:
            event = self._events.get(task_id)
            if event is None:
                # Create an event if missing to allow waiting
                event = threading.Event()
                self._events[task_id] = event
            meta = self._store.get(task_id)
            if meta and meta.get("status") in (SUCCESS, FAILURE):
                return True
        return event.wait(timeout=timeout)


class AsyncResult:
    """
    Minimal AsyncResult-like object with get/successful/failed.
    """
    def __init__(self, app, task_id):
        self.app = app
        self.id = task_id

    def get(self, timeout=None):
        """
        Block until result is ready or timeout occurs. Raise exception on failure.
        """
        backend = self.app.backend
        ready = backend.wait_for(self.id, timeout=timeout)
        if not ready:
            raise TimeoutError("Result not ready before timeout")
        meta = backend.get_task_meta(self.id)
        status = meta.get("status")
        if status == SUCCESS:
            return meta.get("result")
        elif status == FAILURE:
            # Raise the original exception if available
            exc = meta.get("exception")
            if exc is None:
                raise Exception("Task failed")
            raise exc
        elif status in (PENDING, STARTED):
            # Not ready even after wait? treat as timeout
            raise TimeoutError("Result not ready")
        else:
            # Unknown status
            return meta.get("result")

    def ready(self):
        return self.status in (SUCCESS, FAILURE)

    def successful(self):
        return self.status == SUCCESS

    def failed(self):
        return self.status == FAILURE

    @property
    def status(self):
        return self.app.backend.get_task_meta(self.id).get("status", PENDING)

    def __repr__(self):
        return f"<AsyncResult: {self.id} state={self.status}>"


class Task:
    """
    Minimal Task wrapper providing .delay and .apply_async.
    """
    abstract = False

    def __init__(self, app, name, func, bind=False):
        self.app = app
        self.name = name
        self._func = func
        self._bind = bind
        self.request = SimpleNamespace(id=None)

    def __call__(self, *args, **kwargs):
        # Direct call executes the function synchronously, binding if needed.
        if self._bind:
            return self._func(self, *args, **kwargs)
        return self._func(*args, **kwargs)

    def run(self, *args, **kwargs):
        # In Celery, run is the method to override; here we call the function.
        return self.__call__(*args, **kwargs)

    def delay(self, *args, **kwargs):
        return self.apply_async(args=args, kwargs=kwargs)

    def apply_async(self, args=None, kwargs=None, task_id=None, countdown=None, eta=None, **options):
        """
        Minimal apply_async: executes eagerly based on app.conf or memory broker.
        Returns AsyncResult immediately.
        """
        args = args or ()
        kwargs = kwargs or {}
        tid = task_id or uuid4()
        backend = self.app.backend
        backend.store_pending(tid)

        # Determine eager/local execution
        eager = bool(self.app.conf.task_always_eager) or str(self.app.conf.broker_url or "").startswith("memory://")
        if eager:
            backend.store_started(tid)
            self.request = SimpleNamespace(id=tid)
            try:
                res = self.run(*args, **kwargs)
            except Exception as exc:
                # In eager mode, store exception; optionally propagate based on config at get-time.
                backend.store_exception(tid, exc)
            else:
                backend.store_result(tid, res, status=SUCCESS)
        else:
            # Non-eager path: in this minimal implementation, we still run locally.
            backend.store_started(tid)
            self.request = SimpleNamespace(id=tid)
            try:
                res = self.run(*args, **kwargs)
            except Exception as exc:
                backend.store_exception(tid, exc)
            else:
                backend.store_result(tid, res, status=SUCCESS)

        return AsyncResult(self.app, tid)

    def apply(self, args=None, kwargs=None):
        """
        Synchronous apply. Returns an AsyncResult with the completed state.
        """
        return self.apply_async(args=args, kwargs=kwargs)


class Celery:
    """
    Minimal Celery application class with task registration, sending, and eager execution.
    """
    def __init__(self, main=None, broker=None, backend=None, broker_url=None, result_backend=None, config_source=None, **kwargs):
        self.main = main or "__main__"
        # Build configuration
        initial_conf = {}
        if broker_url is not None:
            initial_conf["broker_url"] = broker_url
        elif broker is not None:
            initial_conf["broker"] = broker
        if result_backend is not None:
            initial_conf["result_backend"] = result_backend
        elif backend is not None:
            initial_conf["backend"] = backend

        if isinstance(config_source, dict):
            initial_conf.update(config_source)

        initial_conf.update(kwargs)
        self.conf = Configuration(initial_conf)

        # Result backend (only in-memory for this implementation)
        self.backend = InMemoryBackend()

        # Task registry
        self.tasks = {}

    def task(self, name=None, bind=False, **opts):
        """
        Decorator to register a function as a task.
        Usage:
            @app.task(name="mytask", bind=True)
            def do(self, x): ...
        """
        def decorator(func):
            task_name = name or f"{func.__module__}.{func.__name__}"
            task = Task(self, task_name, func, bind=bind)
            self.register_task(task)
            return task
        return decorator

    def register_task(self, task):
        self.tasks[task.name] = task
        return task

    def send_task(self, name, args=None, kwargs=None, **options):
        """
        Send a task by name. Returns AsyncResult.
        """
        args = args or ()
        kwargs = kwargs or {}
        task = self.tasks.get(name)
        if task is None:
            # Try simple fallback: maybe function name without module
            for tname, t in self.tasks.items():
                if tname.endswith("." + name) or tname == name:
                    task = t
                    break
        if task is None:
            raise KeyError(f"Unknown task {name!r}")
        return task.apply_async(args=args, kwargs=kwargs, **options)

    def AsyncResult(self, task_id):
        return AsyncResult(self, task_id)