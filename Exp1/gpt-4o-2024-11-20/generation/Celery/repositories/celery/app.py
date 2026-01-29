import uuid
from collections import defaultdict
from threading import Thread
from queue import Queue, Empty

class AsyncResult:
    def __init__(self, task_id, task_store):
        self.task_id = task_id
        self.task_store = task_store

    def get(self, timeout=None):
        task = self.task_store.get(self.task_id)
        if task is None:
            raise ValueError("Task not found")
        task['thread'].join(timeout)
        if 'exception' in task:
            raise task['exception']
        return task.get('result')

    def successful(self):
        task = self.task_store.get(self.task_id)
        return task is not None and 'result' in task and 'exception' not in task

    def failed(self):
        task = self.task_store.get(self.task_id)
        return task is not None and 'exception' in task


class Celery:
    def __init__(self, name, broker=None, backend=None):
        self.name = name
        self.broker_url = broker or 'memory://'
        self.result_backend = backend or 'memory://'
        self.conf = {
            'task_always_eager': False,
        }
        self.tasks = {}
        self.task_store = {}
        self.task_queue = Queue()

        if self.broker_url == 'memory://':
            self.worker_thread = Thread(target=self._worker, daemon=True)
            self.worker_thread.start()

    def task(self, name=None, bind=False):
        def decorator(func):
            task_name = name or func.__name__
            self.tasks[task_name] = {
                'func': func,
                'bind': bind,
            }
            return func
        return decorator

    def send_task(self, task_name, args=None, kwargs=None):
        args = args or []
        kwargs = kwargs or {}
        task_id = str(uuid.uuid4())
        self._submit_task(task_name, task_id, args, kwargs)
        return AsyncResult(task_id, self.task_store)

    def _submit_task(self, task_name, task_id, args, kwargs):
        if self.conf.get('task_always_eager', False):
            self._execute_task(task_name, task_id, args, kwargs)
        else:
            self.task_queue.put((task_name, task_id, args, kwargs))

    def _worker(self):
        while True:
            try:
                task_name, task_id, args, kwargs = self.task_queue.get(timeout=1)
                self._execute_task(task_name, task_id, args, kwargs)
            except Empty:
                continue

    def _execute_task(self, task_name, task_id, args, kwargs):
        task = self.tasks.get(task_name)
        if not task:
            raise ValueError(f"Task {task_name} not found")
        func = task['func']
        if task['bind']:
            func = func.__get__(self, Celery)
        try:
            result = func(*args, **kwargs)
            self.task_store[task_id] = {'result': result, 'thread': Thread()}
        except Exception as e:
            self.task_store[task_id] = {'exception': e, 'thread': Thread()}

    def apply_async(self, func, args=None, kwargs=None):
        return self.send_task(func.__name__, args, kwargs)

    def delay(self, func, *args, **kwargs):
        return self.apply_async(func, args, kwargs)