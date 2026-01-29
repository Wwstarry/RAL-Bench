import inspect
import uuid
from functools import partial, wraps
from celery.result import AsyncResult
from celery.exceptions import TaskError

class Task:
    """Task base class."""
    
    abstract = True
    
    def __init__(self, run=None, name=None, app=None, bind=False, **options):
        self.run = run
        if run:
            self.__call__ = self._make_callable()
            self.name = name or self.run.__name__
        else:
            self.name = name
        self.app = app
        self.bind = bind
        self.options = options
        if self.name and app and self.name not in app.tasks:
            app.tasks[self.name] = self
        
    def _make_callable(self):
        """Make the task callable."""
        func = self.run
        
        @wraps(func)
        def call_task(*args, **kwargs):
            if self.bind:
                return func(self, *args, **kwargs)
            return func(*args, **kwargs)
        
        return call_task
    
    def __call__(self, *args, **kwargs):
        if self.run is None:
            raise NotImplementedError("Task has no run method")
        
        if self.bind:
            return self.run(self, *args, **kwargs)
        return self.run(*args, **kwargs)
    
    def delay(self, *args, **kwargs):
        """Shortcut to apply_async using direct arguments."""
        return self.apply_async(args=args, kwargs=kwargs)
    
    def apply_async(self, args=None, kwargs=None, task_id=None, **options):
        """Apply task asynchronously."""
        args = args or []
        kwargs = kwargs or {}
        task_id = task_id or str(uuid.uuid4())
        
        if self.app.conf.task_always_eager:
            # Execute the task immediately
            try:
                result = self(*args, **kwargs)
                self.app._backend.store_result(task_id, result, "SUCCESS")
                return AsyncResult(task_id, backend=self.app._backend)
            except Exception as exc:
                if self.app.conf.task_eager_propagates:
                    raise
                self.app._backend.store_exception(task_id, exc)
                return AsyncResult(task_id, backend=self.app._backend)
        
        # Simplified: just execute in current process
        try:
            result = self(*args, **kwargs)
            self.app._backend.store_result(task_id, result, "SUCCESS")
        except Exception as exc:
            self.app._backend.store_exception(task_id, exc)
        
        return AsyncResult(task_id, backend=self.app._backend)
    
    def apply(self, args=None, kwargs=None, **options):
        """Apply task synchronously."""
        args = args or []
        kwargs = kwargs or {}
        
        # Always execute eagerly
        return self(*args, **kwargs)