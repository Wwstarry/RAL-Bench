"""
Task class implementation
"""

import uuid
from typing import Any, Callable, Optional
from celery.result import AsyncResult


class Task:
    """Task wrapper class"""
    
    def __init__(self, func: Callable, name: str, app, bind: bool = False, **opts):
        self.func = func
        self.name = name
        self.app = app
        self.bind = bind
        self.opts = opts
        
        # Copy function metadata
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
    
    def __call__(self, *args, **kwargs):
        """Execute the task function"""
        if self.bind:
            # Pass self as first argument
            return self.func(self, *args, **kwargs)
        else:
            return self.func(*args, **kwargs)
    
    def delay(self, *args, **kwargs):
        """Shortcut to apply_async with args and kwargs"""
        return self.apply_async(args=args, kwargs=kwargs)
    
    def apply_async(self, args=None, kwargs=None, **options):
        """Apply task asynchronously"""
        args = args or ()
        kwargs = kwargs or {}
        
        task_id = options.get('task_id') or str(uuid.uuid4())
        
        if self.app.conf.task_always_eager:
            # Execute immediately
            result = AsyncResult(task_id, app=self.app)
            try:
                ret_value = self(*args, **kwargs)
                self.app.backend.store_result(task_id, ret_value, 'SUCCESS')
            except Exception as exc:
                self.app.backend.store_result(task_id, exc, 'FAILURE')
                if self.app.conf.task_eager_propagates:
                    raise
            
            return result
        else:
            # Queue the task
            message = {
                'id': task_id,
                'task': self.name,
                'args': args,
                'kwargs': kwargs,
            }
            self.app.broker.publish(message)
            
            # Start worker if not running
            self.app._ensure_worker_running()
            
            return AsyncResult(task_id, app=self.app)
    
    def apply(self, args=None, kwargs=None, **options):
        """Apply task synchronously"""
        args = args or ()
        kwargs = kwargs or {}
        return self(*args, **kwargs)
    
    @property
    def request(self):
        """Task request context (for bound tasks)"""
        # Simplified implementation
        return TaskRequest(self)


class TaskRequest:
    """Task request context"""
    
    def __init__(self, task):
        self.task = task
        self.id = None
        self.args = None
        self.kwargs = None