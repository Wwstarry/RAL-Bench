import inspect
import threading
import time
import uuid
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Union

from celery import result
from celery.exceptions import TaskRevokedError, TimeoutError
from celery.utils.threads import LocalStack


class Celery:
    """Main application class for task queue."""
    
    def __init__(self, main: Optional[str] = None, **kwargs):
        self.main = main
        self.conf = Configuration(self, **kwargs)
        self.tasks: Dict[str, Callable] = {}
        self._pending_results: Dict[str, result.AsyncResult] = {}
        self._result_backend = None
        self._broker_connection = None
        self._eager = False
        self._setup_from_config()
        
    def _setup_from_config(self):
        """Configure from app.conf settings."""
        broker_url = self.conf.get("broker_url") or self.conf.get("broker")
        if broker_url and broker_url.startswith("memory://"):
            self._eager = True
        elif self.conf.get("task_always_eager", False):
            self._eager = True
            
        result_backend = self.conf.get("result_backend")
        if result_backend and result_backend.startswith("cache+memory://"):
            self._result_backend = InMemoryBackend()
            
    def task(self, *args, **kwargs):
        """Decorator for registering tasks."""
        def decorator(func):
            name = kwargs.get("name") or func.__name__
            bind = kwargs.get("bind", False)
            
            if bind:
                def bound_task(*task_args, **task_kwargs):
                    return TaskWrapper(func, self, name)(*task_args, **task_kwargs)
                self.tasks[name] = bound_task
                bound_task.__name__ = func.__name__
                bound_task.__wrapped__ = func
                return bound_task
            else:
                self.tasks[name] = func
                return func
                
        if args and callable(args[0]):
            return decorator(args[0])
        return decorator
        
    def send_task(self, name: str, args=None, kwargs=None, **options):
        """Send task by name."""
        args = args or []
        kwargs = kwargs or {}
        
        if name not in self.tasks:
            raise ValueError(f"Task '{name}' not registered")
            
        task_id = str(uuid.uuid4())
        
        if self._eager:
            # Execute immediately
            try:
                retval = self.tasks[name](*args, **kwargs)
                async_result = result.AsyncResult(task_id, app=self)
                async_result._set_result(retval)
                self._pending_results[task_id] = async_result
                return async_result
            except Exception as exc:
                async_result = result.AsyncResult(task_id, app=self)
                async_result._set_exception(exc)
                self._pending_results[task_id] = async_result
                return async_result
        else:
            # In a real implementation, this would send to broker
            async_result = result.AsyncResult(task_id, app=self)
            self._pending_results[task_id] = async_result
            return async_result
            
    def AsyncResult(self, task_id: str):
        """Get AsyncResult for task ID."""
        return result.AsyncResult(task_id, app=self)


class Configuration:
    """Configuration container."""
    
    def __init__(self, app: Celery, **kwargs):
        self._app = app
        self._data = {
            "broker_url": "memory://",
            "result_backend": None,
            "task_always_eager": False,
            "task_serializer": "json",
            "result_serializer": "json",
            "accept_content": ["json"],
            "result_expires": None,
            "task_track_started": False,
            "task_store_eager_result": True,
        }
        self._data.update(kwargs)
        
    def get(self, key: str, default=None):
        return self._data.get(key, default)
        
    def __getitem__(self, key: str):
        return self._data[key]
        
    def __setitem__(self, key: str, value):
        self._data[key] = value
        
    def update(self, config_dict: Dict[str, Any]):
        self._data.update(config_dict)


class TaskWrapper:
    """Wrapper for bound tasks."""
    
    def __init__(self, func: Callable, app: Celery, name: str):
        self.func = func
        self.app = app
        self.name = name
        
    def __call__(self, *args, **kwargs):
        return self.func(self, *args, **kwargs)
        
    def delay(self, *args, **kwargs):
        return self.apply_async(args, kwargs)
        
    def apply_async(self, args=None, kwargs=None, **options):
        return self.app.send_task(self.name, args, kwargs, **options)


class InMemoryBackend:
    """Simple in-memory result backend."""
    
    def __init__(self):
        self._results: Dict[str, Any] = {}
        self._lock = threading.Lock()
        
    def store_result(self, task_id: str, result: Any, state: str):
        with self._lock:
            self._results[task_id] = {"result": result, "state": state}
            
    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._results.get(task_id)