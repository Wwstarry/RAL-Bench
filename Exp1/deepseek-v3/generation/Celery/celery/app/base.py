"""Celery application base"""

import uuid
import time
import threading
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum


class TaskState(Enum):
    PENDING = 'PENDING'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    RETRY = 'RETRY'
    REVOKED = 'REVOKED'


@dataclass
class TaskMessage:
    id: str
    task: str
    args: tuple
    kwargs: dict
    retries: int = 0
    eta: Optional[float] = None
    expires: Optional[float] = None


class AsyncResult:
    """Result of an asynchronous task"""
    
    def __init__(self, task_id: str, app: 'Celery'):
        self.id = task_id
        self.app = app
        self._result = None
        self._state = TaskState.PENDING
        self._exception = None
    
    def get(self, timeout: Optional[float] = None, propagate: bool = True) -> Any:
        """Get task result"""
        if self._state == TaskState.PENDING:
            # Wait for task completion
            start_time = time.time()
            while self._state == TaskState.PENDING:
                if timeout and (time.time() - start_time) > timeout:
                    raise TimeoutError(f"Timeout waiting for task {self.id}")
                time.sleep(0.01)
        
        if self._state == TaskState.SUCCESS:
            return self._result
        elif self._state == TaskState.FAILURE and propagate:
            raise self._exception if self._exception else Exception("Task failed")
        elif self._state == TaskState.FAILURE:
            return self._exception
        else:
            return None
    
    def successful(self) -> bool:
        """Return True if the task executed successfully"""
        return self._state == TaskState.SUCCESS
    
    def failed(self) -> bool:
        """Return True if the task failed"""
        return self._state == TaskState.FAILURE
    
    def ready(self) -> bool:
        """Return True if the task has been executed"""
        return self._state in (TaskState.SUCCESS, TaskState.FAILURE)
    
    def state(self) -> str:
        """Return current task state"""
        return self._state.value
    
    def _set_result(self, result: Any, state: TaskState, exception: Optional[Exception] = None):
        """Internal method to set task result"""
        self._result = result
        self._state = state
        self._exception = exception


class Task:
    """Task base class"""
    
    def __init__(self, name: str, func: Callable, app: 'Celery', bind: bool = False):
        self.name = name
        self.func = func
        self.app = app
        self.bind = bind
    
    def __call__(self, *args, **kwargs):
        """Direct synchronous execution"""
        return self.func(*args, **kwargs)
    
    def delay(self, *args, **kwargs) -> AsyncResult:
        """Shortcut to apply_async"""
        return self.apply_async(args, kwargs)
    
    def apply_async(self, args: Optional[tuple] = None, kwargs: Optional[dict] = None, 
                   **options) -> AsyncResult:
        """Execute task asynchronously"""
        args = args or ()
        kwargs = kwargs or {}
        
        if self.app.conf.task_always_eager:
            # Eager execution mode
            return self._execute_eager(args, kwargs)
        else:
            # Async execution
            return self.app.backend.send_task(self.name, args, kwargs, **options)
    
    def _execute_eager(self, args: tuple, kwargs: dict) -> AsyncResult:
        """Execute task eagerly (synchronously)"""
        task_id = str(uuid.uuid4())
        result = AsyncResult(task_id, self.app)
        
        try:
            if self.bind:
                # Bind the task instance as first argument
                bound_args = (self,) + args
                task_result = self.func(*bound_args, **kwargs)
            else:
                task_result = self.func(*args, **kwargs)
            
            result._set_result(task_result, TaskState.SUCCESS)
        except Exception as e:
            result._set_result(None, TaskState.FAILURE, e)
        
        return result


class Configuration:
    """Application configuration"""
    
    def __init__(self):
        self._data = {
            'broker_url': 'memory://',
            'result_backend': 'cache+memory://',
            'task_always_eager': False,
            'task_eager_propagates': True,
            'task_serializer': 'json',
            'result_serializer': 'json',
            'accept_content': ['json'],
            'timezone': 'UTC',
            'enable_utc': True,
        }
    
    def __getitem__(self, key):
        return self._data[key]
    
    def __setitem__(self, key, value):
        self._data[key] = value
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def update(self, config_dict: dict):
        self._data.update(config_dict)


class MemoryBackend:
    """In-memory backend for testing"""
    
    def __init__(self, app: 'Celery'):
        self.app = app
        self.tasks: Dict[str, AsyncResult] = {}
        self._lock = threading.Lock()
    
    def send_task(self, task_name: str, args: tuple, kwargs: dict, **options) -> AsyncResult:
        """Send task to be executed"""
        task_id = str(uuid.uuid4())
        result = AsyncResult(task_id, self.app)
        
        with self._lock:
            self.tasks[task_id] = result
        
        # Execute immediately in separate thread for async behavior
        def execute_task():
            try:
                task_func = self.app.tasks[task_name]
                if hasattr(task_func, 'func'):
                    # It's a decorated function
                    task_result = task_func.func(*args, **kwargs)
                else:
                    # It's a regular function
                    task_result = task_func(*args, **kwargs)
                
                result._set_result(task_result, TaskState.SUCCESS)
            except Exception as e:
                result._set_result(None, TaskState.FAILURE, e)
        
        threading.Thread(target=execute_task, daemon=True).start()
        return result


class Celery:
    """Celery application"""
    
    def __init__(self, name: str = None, **kwargs):
        self.name = name or 'celery'
        self.conf = Configuration()
        self.tasks: Dict[str, Task] = {}
        self.backend = MemoryBackend(self)
        
        # Update configuration
        if kwargs:
            self.conf.update(kwargs)
    
    def task(self, func: Callable = None, **options):
        """Decorator to register a task"""
        def _inner(f):
            name = options.get('name', f.__name__)
            bind = options.get('bind', False)
            task = Task(name, f, self, bind)
            self.tasks[name] = task
            
            # Make the task callable
            return task
        
        if func is None:
            return _inner
        return _inner(func)
    
    def send_task(self, name: str, args: tuple = None, kwargs: dict = None, **options) -> AsyncResult:
        """Send task by name"""
        args = args or ()
        kwargs = kwargs or {}
        
        if name not in self.tasks:
            raise ValueError(f"Task '{name}' not registered")
        
        return self.tasks[name].apply_async(args, kwargs, **options)


# Create default app instance
current_app = Celery()