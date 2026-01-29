import threading
import time
import uuid
import inspect
import functools
import queue

class AsyncResult:
    def __init__(self, task_id, backend):
        self.task_id = task_id
        self._backend = backend

    def get(self, timeout=None):
        return self._backend.get_result(self.task_id, timeout=timeout)

    def successful(self):
        return self._backend.is_successful(self.task_id)

    def failed(self):
        return self._backend.is_failed(self.task_id)


class Task:
    def __init__(self, app, func, name=None, bind=False):
        self.app = app
        self.func = func
        self.name = name or func.__name__
        self.bind = bind
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        if self.bind:
            return self.func(self, *args, **kwargs)
        else:
            return self.func(*args, **kwargs)

    def delay(self, *args, **kwargs):
        return self.apply_async(args=args, kwargs=kwargs)

    def apply_async(self, args=None, kwargs=None):
        args = args or ()
        kwargs = kwargs or {}
        task_id = str(uuid.uuid4())
        if self.app.conf.task_always_eager:
            # eager mode: execute immediately
            try:
                if self.bind:
                    result = self.func(self, *args, **kwargs)
                else:
                    result = self.func(*args, **kwargs)
                self.app.backend.store_result(task_id, result, success=True)
            except Exception as exc:
                self.app.backend.store_result(task_id, exc, success=False)
            return AsyncResult(task_id, self.app.backend)
        else:
            # enqueue task for broker
            self.app.broker.send_task(self.name, task_id, args, kwargs)
            return AsyncResult(task_id, self.app.backend)


class Config:
    def __init__(self):
        self.task_always_eager = False
        self.result_backend = None
        self.broker_url = None
        self.task_eager_propagates = False


class InMemoryBroker:
    def __init__(self, app):
        self.app = app
        self.tasks_queue = queue.Queue()
        self._worker_thread = None
        self._stop_event = threading.Event()

    def send_task(self, task_name, task_id, args, kwargs):
        self.tasks_queue.put((task_name, task_id, args, kwargs))

    def start_worker(self):
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._stop_event.clear()
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker_thread.start()

    def stop_worker(self):
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join()
            self._worker_thread = None

    def _worker_loop(self):
        while not self._stop_event.is_set():
            try:
                task_name, task_id, args, kwargs = self.tasks_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            task = self.app.tasks.get(task_name)
            if not task:
                # unknown task, store failure
                self.app.backend.store_result(task_id, Exception(f"Unknown task {task_name}"), success=False)
                continue
            try:
                if task.bind:
                    result = task.func(task, *args, **kwargs)
                else:
                    result = task.func(*args, **kwargs)
                self.app.backend.store_result(task_id, result, success=True)
            except Exception as exc:
                self.app.backend.store_result(task_id, exc, success=False)


class InMemoryBackend:
    def __init__(self):
        self._results = {}
        self._results_lock = threading.Lock()
        self._result_events = {}

    def store_result(self, task_id, result, success=True):
        with self._results_lock:
            self._results[task_id] = (success, result)
            event = self._result_events.get(task_id)
            if event:
                event.set()

    def get_result(self, task_id, timeout=None):
        with self._results_lock:
            if task_id in self._results:
                success, result = self._results[task_id]
                if success:
                    return result
                else:
                    raise result
            else:
                event = self._result_events.get(task_id)
                if not event:
                    event = threading.Event()
                    self._result_events[task_id] = event

        waited = event.wait(timeout)
        if not waited:
            raise TimeoutError(f"Timeout waiting for task {task_id} result")

        with self._results_lock:
            success, result = self._results.get(task_id, (False, Exception("No result found")))
            if success:
                return result
            else:
                raise result

    def is_successful(self, task_id):
        with self._results_lock:
            if task_id in self._results:
                success, _ = self._results[task_id]
                return success
            return False

    def is_failed(self, task_id):
        with self._results_lock:
            if task_id in self._results:
                success, _ = self._results[task_id]
                return not success
            return False


class Celery:
    def __init__(self, main=None, broker=None, backend=None, broker_url=None, result_backend=None):
        self.main = main
        self.tasks = {}
        self.conf = Config()
        # Configure broker_url and result_backend
        self.conf.broker_url = broker_url or broker or None
        self.conf.result_backend = result_backend or backend or None

        # Eager mode default false
        self.conf.task_always_eager = False
        self.conf.task_eager_propagates = False

        # Setup backend
        if self.conf.result_backend in (None, '', 'memory://'):
            self.backend = InMemoryBackend()
        else:
            # For now, only support memory backend
            self.backend = InMemoryBackend()

        # Setup broker
        if self.conf.broker_url in (None, '', 'memory://'):
            self.broker = InMemoryBroker(self)
            self.broker.start_worker()
        else:
            # For now, only support memory broker
            self.broker = InMemoryBroker(self)
            self.broker.start_worker()

    def task(self, *args, **kwargs):
        # Support @app.task or @app.task(...)
        if len(args) == 1 and callable(args[0]) and not kwargs:
            # Used as @app.task
            func = args[0]
            return self._register_task(func, **kwargs)
        else:
            # Used as @app.task(...)
            def decorator(func):
                return self._register_task(func, **kwargs)
            return decorator

    def _register_task(self, func, name=None, bind=False):
        task_name = name or func.__name__
        if task_name in self.tasks:
            # overwrite existing task
            pass
        task = Task(self, func, name=task_name, bind=bind)
        self.tasks[task_name] = task
        return task

    def send_task(self, name, args=None, kwargs=None):
        args = args or ()
        kwargs = kwargs or {}
        task = self.tasks.get(name)
        if self.conf.task_always_eager:
            # eager mode: execute immediately
            task_id = str(uuid.uuid4())
            try:
                if task is None:
                    raise Exception(f"Unknown task {name}")
                if task.bind:
                    result = task.func(task, *args, **kwargs)
                else:
                    result = task.func(*args, **kwargs)
                self.backend.store_result(task_id, result, success=True)
            except Exception as exc:
                self.backend.store_result(task_id, exc, success=False)
            return AsyncResult(task_id, self.backend)
        else:
            # enqueue task
            task_id = str(uuid.uuid4())
            self.broker.send_task(name, task_id, args, kwargs)
            return AsyncResult(task_id, self.backend)