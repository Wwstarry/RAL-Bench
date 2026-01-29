"""
Celery Application
"""

import inspect
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from . import current_app
from .exceptions import TimeoutError
from .utils import cached_property


class TaskState(Enum):
    """Task execution states."""
    PENDING = 'PENDING'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    RETRY = 'RETRY'
    REVOKED = 'REVOKED'


@dataclass
class AsyncResult:
    """Result handle for an asynchronous task."""
    id: str
    app: 'Celery'
    
    def __init__(self, id: str, app: 'Celery'):
        self.id = id
        self.app = app
    
    def get(self, timeout: Optional[float] = None, propagate: bool = True) -> Any:
        """Wait for and return the task result."""
        start_time = time.time()
        while True:
            result = self.app.backend.get_result(self.id)
            if result is not None:
                state, value = result
                if state == TaskState.SUCCESS:
                    return value
                elif state == TaskState.FAILURE:
                    if propagate:
                        raise value
                    return value
                elif state == TaskState.REVOKED:
                    raise Exception(f'Task {self.id} revoked')
            
            if timeout is not None and (time.time() - start_time) > timeout:
                raise TimeoutError('The operation timed out.')
            
            time.sleep(0.01)
    
    def successful(self) -> bool:
        """Return True if the task executed successfully."""
        result = self.app.backend.get_result(self.id)
        if result is None:
            return False
        state, _ = result
        return state == TaskState.SUCCESS
    
    def failed(self) -> bool:
        """Return True if the task failed."""
        result = self.app.backend.get_result(self.id)
        if result is None:
            return False
        state, _ = result
        return state == TaskState.FAILURE
    
    def ready(self) -> bool:
        """Return True if the task has been executed."""
        return self.app.backend.get_result(self.id) is not None
    
    def state(self) -> str:
        """Return the current task state."""
        result = self.app.backend.get_result(self.id)
        if result is None:
            return TaskState.PENDING.value
        state, _ = result
        return state.value
    
    @property
    def status(self) -> str:
        """Alias for state."""
        return self.state()


class Backend:
    """Base result backend."""
    
    def __init__(self, app: 'Celery'):
        self.app = app
        self.results: Dict[str, Tuple[TaskState, Any]] = {}
        self.lock = threading.Lock()
    
    def store_result(self, task_id: str, result: Any, state: TaskState):
        """Store a task result."""
        with self.lock:
            self.results[task_id] = (state, result)
    
    def get_result(self, task_id: str) -> Optional[Tuple[TaskState, Any]]:
        """Retrieve a task result."""
        with self.lock:
            return self.results.get(task_id)


class Task:
    """Task base class."""
    
    def __init__(self, func: Callable, app: 'Celery', name: Optional[str] = None, 
                 bind: bool = False, **options):
        self.func = func
        self.app = app
        self.name = name or self._gen_task_name(func)
        self.bind = bind
        self.options = options
        
        # Register with app
        self.app.tasks[self.name] = self
    
    def _gen_task_name(self, func: Callable) -> str:
        """Generate task name from function."""
        module = func.__module__
        name = func.__name__
        return f'{module}.{name}' if module else name
    
    def __call__(self, *args, **kwargs):
        """Execute task synchronously."""
        return self.run(*args, **kwargs)
    
    def run(self, *args, **kwargs):
        """Execute the task function."""
        if self.bind:
            # Create a bound task instance
            return self.func(self, *args, **kwargs)
        return self.func(*args, **kwargs)
    
    def delay(self, *args, **kwargs) -> AsyncResult:
        """Shortcut to apply_async."""
        return self.apply_async(args, kwargs)
    
    def apply_async(self, args: Tuple = None, kwargs: Dict = None, 
                   **options) -> AsyncResult:
        """Apply task asynchronously."""
        args = args or ()
        kwargs = kwargs or {}
        
        # Merge task options with call options
        call_options = {**self.options, **options}
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Send to broker
        self.app.broker.send_task(
            task_id=task_id,
            task_name=self.name,
            args=args,
            kwargs=kwargs,
            **call_options
        )
        
        return AsyncResult(task_id, self.app)
    
    def apply(self, args: Tuple = None, kwargs: Dict = None):
        """Apply task synchronously."""
        args = args or ()
        kwargs = kwargs or {}
        return self.run(*args, **kwargs)


class Broker:
    """Base message broker."""
    
    def __init__(self, app: 'Celery'):
        self.app = app
        self.workers: List['Worker'] = []
        self.task_queue = []
        self.lock = threading.Lock()
        self.worker_thread = None
    
    def send_task(self, task_id: str, task_name: str, args: Tuple, 
                  kwargs: Dict, **options):
        """Send task to broker."""
        with self.lock:
            self.task_queue.append({
                'id': task_id,
                'task': task_name,
                'args': args,
                'kwargs': kwargs,
                'options': options
            })
        
        # Start worker thread if not running
        if not self.worker_thread or not self.worker_thread.is_alive():
            self._start_worker()
    
    def _start_worker(self):
        """Start worker thread."""
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
    
    def _worker_loop(self):
        """Worker processing loop."""
        while True:
            task = None
            with self.lock:
                if self.task_queue:
                    task = self.task_queue.pop(0)
            
            if task:
                self._process_task(task)
            else:
                time.sleep(0.01)
    
    def _process_task(self, task: Dict):
        """Process a single task."""
        task_id = task['id']
        task_name = task['task']
        args = task['args']
        kwargs = task['kwargs']
        
        # Get task from registry
        task_obj = self.app.tasks.get(task_name)
        if not task_obj:
            # Task not registered, try to find it
            for registered_task in self.app.tasks.values():
                if registered_task.name == task_name:
                    task_obj = registered_task
                    break
        
        if not task_obj:
            # Store failure
            self.app.backend.store_result(
                task_id,
                Exception(f'Task {task_name} not found'),
                TaskState.FAILURE
            )
            return
        
        # Store started state
        self.app.backend.store_result(task_id, None, TaskState.STARTED)
        
        try:
            # Execute task
            result = task_obj.run(*args, **kwargs)
            # Store success
            self.app.backend.store_result(task_id, result, TaskState.SUCCESS)
        except Exception as e:
            # Store failure
            self.app.backend.store_result(task_id, e, TaskState.FAILURE)


class Config:
    """Application configuration."""
    
    def __init__(self):
        self._data = {
            'broker_url': 'memory://',
            'result_backend': 'memory://',
            'task_always_eager': False,
            'task_eager_propagates': False,
            'task_serializer': 'json',
            'result_serializer': 'json',
            'accept_content': ['json'],
            'result_expires': None,
            'result_cache_max': 10000,
            'task_track_started': True,
            'task_store_eager_result': True,
            'worker_prefetch_multiplier': 4,
            'worker_max_tasks_per_child': None,
            'worker_disable_rate_limits': False,
        }
    
    def __getitem__(self, key: str) -> Any:
        return self._data.get(key)
    
    def __setitem__(self, key: str, value: Any):
        self._data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)
    
    def update(self, config: Dict):
        self._data.update(config)
    
    def __contains__(self, key: str) -> bool:
        return key in self._data
    
    def __repr__(self) -> str:
        return f'<Config: {self._data}>'


class Celery:
    """Celery application."""
    
    def __init__(self, main: Optional[str] = None, **kwargs):
        self.main = main
        self.conf = Config()
        self.tasks: Dict[str, Task] = {}
        
        # Update config from kwargs
        config_updates = {}
        for key, value in kwargs.items():
            if key in ['broker', 'broker_url']:
                config_updates['broker_url'] = value
            elif key in ['backend', 'result_backend']:
                config_updates['result_backend'] = value
            else:
                config_updates[key] = value
        
        self.conf.update(config_updates)
        
        # Initialize components
        self.broker = Broker(self)
        self.backend = Backend(self)
        
        # Set as current app
        self.set_current()
    
    def set_current(self):
        """Set this as the current app."""
        current_app._set_current_app(self)
    
    def task(self, *args, **kwargs):
        """Decorator to create a task."""
        def decorator(func):
            return Task(func, self, *args, **kwargs)
        
        if args and callable(args[0]):
            # Used as @app.task
            return decorator(args[0])
        return decorator
    
    def send_task(self, name: str, args: Tuple = None, kwargs: Dict = None, 
                 **options) -> AsyncResult:
        """Send task by name."""
        args = args or ()
        kwargs = kwargs or {}
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Send to broker
        self.broker.send_task(
            task_id=task_id,
            task_name=name,
            args=args,
            kwargs=kwargs,
            **options
        )
        
        return AsyncResult(task_id, self)
    
    @property
    def current_task(self):
        """Get the currently executing task."""
        # Simplified implementation
        return None
    
    def config_from_object(self, obj: Any):
        """Load configuration from object."""
        if isinstance(obj, dict):
            self.conf.update(obj)
        elif hasattr(obj, '__dict__'):
            config = {}
            for key in dir(obj):
                if not key.startswith('_'):
                    value = getattr(obj, key)
                    if not callable(value):
                        config[key] = value
            self.conf.update(config)
    
    def finalize(self):
        """Finalize app setup."""
        pass
    
    def start(self):
        """Start the app."""
        pass
    
    def close(self):
        """Close the app."""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, *exc_info):
        self.close()