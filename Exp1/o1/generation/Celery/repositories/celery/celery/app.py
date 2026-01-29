"""
Minimal Celery-like application entrypoint.
"""

import types
from functools import wraps

from .config import Config
from .task import Task
from .result import AsyncResult

class Celery:
    """
    A minimal Celery-compatible application.
    Maintains task registry, configuration, and provides task creation utilities.
    """

    def __init__(self, main=None, broker=None, backend=None, **kwargs):
        self.main = main
        self.conf = Config()
        if broker:
            self.conf["broker_url"] = broker
        if backend:
            self.conf["result_backend"] = backend
        self.conf.update(kwargs)
        self._tasks = {}

    @property
    def Task(self):
        """
        Return the base Task class used by this app.
        """
        return Task

    def task(self, *args, **opts):
        """
        Decorator to create a Task and register it in the app.
        Usage:
            @app.task(name="mytask", bind=True)
            def mytask(...):
                ...
        """
        def decorator(func):
            # If it's a class-based definition or a normal function, adapt
            task_name = opts.get("name") or func.__name__
            bind = opts.get("bind", False)

            # Create a new Task subclass around `func`
            class ConcreteTask(self.Task):
                name = task_name
                _bind = bind
                app = self

                def run(self_or_self, *f_args, **f_kwargs):
                    if bind:
                        return func(self_or_self, *f_args, **f_kwargs)
                    return func(*f_args, **f_kwargs)

            # We can store a reference to the original function if needed
            ConcreteTask.__doc__ = func.__doc__
            ConcreteTask.__name__ = func.__name__
            ctask = ConcreteTask()

            # Register the task
            self._tasks[task_name] = ctask
            return ctask

        if len(args) == 1 and callable(args[0]):
            # Decorator used as @app.task without params
            return decorator(args[0])
        return decorator

    def send_task(self, name, args=None, kwargs=None, **options):
        """
        Send a task by name. Returns an AsyncResult.
        """
        args = args or ()
        kwargs = kwargs or {}
        task = self._tasks.get(name)
        if not task:
            # In a real Celery environment we might raise a specific exception
            raise ValueError(f"Task '{name}' not registered.")
        return task.apply_async(args=args, kwargs=kwargs, **options)