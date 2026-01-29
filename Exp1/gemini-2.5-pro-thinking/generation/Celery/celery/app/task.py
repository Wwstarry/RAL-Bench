import traceback
from ..utils import gen_unique_id
from ..result import AsyncResult

class Task:
    def __init__(self, func, app, name=None, bind=False, **kwargs):
        self.func = func
        self.app = app
        self.name = name or (app.gen_task_name(func.__name__, func.__module__) if app else f"{func.__module__}.{func.__name__}")
        self.bind = bind
        self._decorated = func

    def __call__(self, *args, **kwargs):
        """Execute the task's logic."""
        if self.bind:
            return self.func(self, *args, **kwargs)
        return self.func(*args, **kwargs)

    def delay(self, *args, **kwargs):
        """Shortcut for apply_async with positional arguments."""
        return self.apply_async(args=args, kwargs=kwargs)

    def apply_async(self, args=None, kwargs=None, task_id=None, **options):
        """
        Execute the task.
        
        In this implementation, execution is always local and synchronous
        to satisfy the "no external services" requirement. The result is
        stored in the backend, and an AsyncResult is returned, mimicking
        the API of a distributed setup.
        """
        if self.app is None:
            raise TypeError('Task must be bound to an app to be called.')

        args = args or ()
        kwargs = kwargs or {}
        task_id = task_id or gen_unique_id()

        try:
            result = self(*args, **kwargs)
            state = "SUCCESS"
            tb = None
        except Exception as e:
            result = e
            state = "FAILURE"
            tb = traceback.format_exc()

        self.app.backend.store_result(task_id, result, state, traceback=tb)
        return AsyncResult(task_id, self.app.backend)

    def __get__(self, obj, objtype=None):
        """Support for tasks defined as methods on a class."""
        if obj is None:
            return self
        return self.__class__(self._decorated, self.app, name=self.name, bind=self.bind)