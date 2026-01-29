"""
Celery application base class
"""

import threading
import uuid
from typing import Any, Callable, Dict, Optional, List, Tuple
from celery.result import AsyncResult
from celery.app.task import Task
from celery.backends.base import BaseBackend
from celery.backends.memory import MemoryBackend
from celery.brokers.base import BaseBroker
from celery.brokers.memory import MemoryBroker
from celery.worker import Worker


class Celery:
    """Main Celery application class"""
    
    def __init__(self, main=None, broker=None, backend=None, 
                 broker_url=None, result_backend=None, **kwargs):
        self.main = main or 'celery'
        self._tasks = {}
        self._broker = None
        self._backend = None
        self._worker = None
        self._worker_thread = None
        
        # Configuration
        self.conf = CeleryConfig()
        
        # Set broker
        broker_url = broker_url or broker or 'memory://'
        self.conf.broker_url = broker_url
        
        # Set backend
        result_backend = result_backend or backend or 'memory://'
        self.conf.result_backend = result_backend
        
        # Apply any additional config
        for key, value in kwargs.items():
            setattr(self.conf, key, value)
    
    @property
    def broker(self):
        """Get or create broker instance"""
        if self._broker is None:
            self._broker = self._create_broker()
        return self._broker
    
    @property
    def backend(self):
        """Get or create backend instance"""
        if self._backend is None:
            self._backend = self._create_backend()
        return self._backend
    
    def _create_broker(self):
        """Create broker based on configuration"""
        broker_url = self.conf.broker_url
        if broker_url.startswith('memory://'):
            return MemoryBroker()
        # Add other broker types as needed
        return MemoryBroker()
    
    def _create_backend(self):
        """Create backend based on configuration"""
        backend_url = self.conf.result_backend
        if backend_url.startswith('memory://'):
            return MemoryBackend()
        # Add other backend types as needed
        return MemoryBackend()
    
    def task(self, *args, **opts):
        """Decorator to register a task"""
        def decorator(func):
            name = opts.get('name') or f'{self.main}.{func.__name__}'
            bind = opts.get('bind', False)
            
            task = Task(
                func=func,
                name=name,
                app=self,
                bind=bind,
                **opts
            )
            
            self._tasks[name] = task
            return task
        
        # Handle both @app.task and @app.task()
        if len(args) == 1 and callable(args[0]):
            return decorator(args[0])
        return decorator
    
    def send_task(self, name, args=None, kwargs=None, **options):
        """Send task by name"""
        args = args or ()
        kwargs = kwargs or {}
        
        task_id = str(uuid.uuid4())
        
        if self.conf.task_always_eager:
            # Execute immediately
            task = self._tasks.get(name)
            if task is None:
                raise KeyError(f'Task {name} not registered')
            
            result = AsyncResult(task_id, app=self)
            try:
                ret_value = task(*args, **kwargs)
                self.backend.store_result(task_id, ret_value, 'SUCCESS')
            except Exception as exc:
                self.backend.store_result(task_id, exc, 'FAILURE')
            
            return result
        else:
            # Queue the task
            message = {
                'id': task_id,
                'task': name,
                'args': args,
                'kwargs': kwargs,
            }
            self.broker.publish(message)
            
            # Start worker if not running
            self._ensure_worker_running()
            
            return AsyncResult(task_id, app=self)
    
    def _ensure_worker_running(self):
        """Ensure worker thread is running"""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._worker = Worker(self)
            self._worker_thread = threading.Thread(target=self._worker.run, daemon=True)
            self._worker_thread.start()
    
    def Worker(self, **kwargs):
        """Create a worker instance"""
        return Worker(self, **kwargs)


class CeleryConfig:
    """Configuration object for Celery"""
    
    def __init__(self):
        self.broker_url = 'memory://'
        self.result_backend = 'memory://'
        self.task_always_eager = False
        self.task_eager_propagates = True
        self.result_expires = 86400
        self.task_serializer = 'json'
        self.result_serializer = 'json'
        self.accept_content = ['json']
        self.timezone = 'UTC'
        self.enable_utc = True
        self.task_track_started = False
        self.task_ignore_result = False
        self.worker_prefetch_multiplier = 4
        self.worker_max_tasks_per_child = None
    
    def update(self, **kwargs):
        """Update configuration"""
        for key, value in kwargs.items():
            setattr(self, key, value)