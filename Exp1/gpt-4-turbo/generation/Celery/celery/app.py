import threading
import uuid
import time
import traceback

from .result import AsyncResult
from .config import Config
from . import registry

class Celery:
    def __init__(self, main=None, broker=None, backend=None, **kwargs):
        self.main = main or __name__
        self.conf = Config()
        if broker:
            self.conf.broker_url = broker
        if backend:
            self.conf.result_backend = backend
        for k, v in kwargs.items():
            setattr(self.conf, k, v)
        self._tasks = registry.TaskRegistry()
        self._results = {}
        self._broker = self._get_broker()
        self._backend = self._get_backend()
        self._eager = getattr(self.conf, 'task_always_eager', False)

    def task(self, *args, **opts):
        def decorator(func):
            name = opts.get('name') or f"{func.__module__}.{func.__name__}"
            bind = opts.get('bind', False)
            TaskCls = type(
                func.__name__,
                (Task,),
                {
                    'run': staticmethod(func),
                    'name': name,
                    'app': self,
                    'bind': bind,
                }
            )
            task_instance = TaskCls()
            self._tasks.register(task_instance)
            return task_instance
        if args and callable(args[0]):
            return decorator(args[0])
        return decorator

    def send_task(self, name, args=None, kwargs=None, **opts):
        args = args or ()
        kwargs = kwargs or {}
        task = self._tasks.get(name)
        if not task:
            raise ValueError(f"Task {name} not found")
        return task.apply_async(args=args, kwargs=kwargs)

    def _get_broker(self):
        url = getattr(self.conf, 'broker_url', None)
        if not url or url.startswith('memory://'):
            from .broker import InMemoryBroker
            return InMemoryBroker()
        raise NotImplementedError("Only memory:// broker is supported in pure Python mode.")

    def _get_backend(self):
        url = getattr(self.conf, 'result_backend', None)
        if not url or url.startswith('memory://'):
            from .backend import InMemoryBackend
            return InMemoryBackend(self._results)
        raise NotImplementedError("Only memory:// backend is supported in pure Python mode.")

    def worker_main(self):
        # For test mode: run all pending tasks in broker
        while True:
            message = self._broker.get_message()
            if not message:
                break
            task_name = message['task']
            args = message.get('args', ())
            kwargs = message.get('kwargs', {})
            task = self._tasks.get(task_name)
            if not task:
                continue
            task._execute(args, kwargs, message['id'])

class Task:
    abstract = True
    name = None
    app = None
    bind = False

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def delay(self, *args, **kwargs):
        return self.apply_async(args=args, kwargs=kwargs)

    def apply_async(self, args=None, kwargs=None, **opts):
        args = args or ()
        kwargs = kwargs or {}
        task_id = str(uuid.uuid4())
        app = self.app
        eager = getattr(app.conf, 'task_always_eager', False)
        if eager:
            return self._execute(args, kwargs, task_id)
        message = {
            'task': self.name,
            'args': args,
            'kwargs': kwargs,
            'id': task_id,
        }
        app._broker.put_message(message)
        return AsyncResult(task_id, app._backend)

    def _execute(self, args, kwargs, task_id):
        app = self.app
        backend = app._backend
        try:
            if self.bind:
                result = self.run(self, *args, **kwargs)
            else:
                result = self.run(*args, **kwargs)
            backend.store_result(task_id, result, 'SUCCESS')
            return AsyncResult(task_id, backend)
        except Exception as exc:
            tb = traceback.format_exc()
            backend.store_result(task_id, exc, 'FAILURE', traceback=tb)
            return AsyncResult(task_id, backend)

    def run(self, *args, **kwargs):
        raise NotImplementedError("Task must define a run() method.")