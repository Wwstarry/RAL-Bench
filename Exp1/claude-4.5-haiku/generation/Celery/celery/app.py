import uuid
import time
from typing import Any, Callable, Dict, Optional, Tuple
from celery.result import AsyncResult
from celery.task import Task
from celery.registry import TaskRegistry
from celery.config import Config
from celery.backends.base import BaseBackend
from celery.backends.memory import MemoryBackend
from celery.brokers.base import BaseBroker
from celery.brokers.memory import MemoryBroker


class Celery:
    def __init__(self, main: str = "celery", broker: Optional[str] = None, backend: Optional[str] = None):
        self.main = main
        self.conf = Config()
        self.registry = TaskRegistry()
        
        broker_url = broker or self.conf.get("broker_url", "memory://")
        result_backend = backend or self.conf.get("result_backend", "memory://")
        
        self.conf.broker_url = broker_url
        self.conf.result_backend = result_backend
        
        self._broker = self._get_broker(broker_url)
        self._backend = self._get_backend(result_backend)
    
    def _get_broker(self, broker_url: str) -> BaseBroker:
        if broker_url.startswith("memory://"):
            return MemoryBroker()
        raise ValueError(f"Unsupported broker: {broker_url}")
    
    def _get_backend(self, backend_url: str) -> BaseBackend:
        if backend_url.startswith("memory://"):
            return MemoryBackend()
        raise ValueError(f"Unsupported backend: {backend_url}")
    
    def task(self, *args, **kwargs) -> Callable:
        def decorator(func: Callable) -> Task:
            name = kwargs.get("name", f"{self.main}.{func.__name__}")
            bind = kwargs.get("bind", False)
            
            task = Task(
                func=func,
                name=name,
                app=self,
                bind=bind,
            )
            self.registry.register(task)
            return task
        
        if len(args) == 1 and callable(args[0]) and not kwargs:
            func = args[0]
            name = f"{self.main}.{func.__name__}"
            task = Task(func=func, name=name, app=self, bind=False)
            self.registry.register(task)
            return task
        
        return decorator
    
    def send_task(self, name: str, args: Tuple = (), kwargs: Optional[Dict] = None, **options) -> AsyncResult:
        if kwargs is None:
            kwargs = {}
        
        task = self.registry.get(name)
        if task is None:
            raise ValueError(f"Task {name} not found")
        
        task_id = str(uuid.uuid4())
        
        if self.conf.task_always_eager:
            result = self._execute_task(task, task_id, args, kwargs)
            return AsyncResult(task_id, app=self, result=result, state="SUCCESS")
        
        self._broker.put_message(task_id, name, args, kwargs)
        return AsyncResult(task_id, app=self)
    
    def _execute_task(self, task: Task, task_id: str, args: Tuple, kwargs: Dict) -> Any:
        try:
            if task.bind:
                result = task.func(task, *args, **kwargs)
            else:
                result = task.func(*args, **kwargs)
            self._backend.set_result(task_id, result, "SUCCESS")
            return result
        except Exception as e:
            self._backend.set_result(task_id, str(e), "FAILURE")
            raise
    
    def process_tasks(self):
        while True:
            message = self._broker.get_message()
            if message is None:
                break
            
            task_id, name, args, kwargs = message
            task = self.registry.get(name)
            
            if task is None:
                self._backend.set_result(task_id, f"Task {name} not found", "FAILURE")
                continue
            
            try:
                result = self._execute_task(task, task_id, args, kwargs)
            except Exception as e:
                self._backend.set_result(task_id, str(e), "FAILURE")