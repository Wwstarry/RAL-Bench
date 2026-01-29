from typing import Any, Callable, Dict, Optional, Tuple
from celery.result import AsyncResult
import uuid


class Task:
    def __init__(self, func: Callable, name: str, app: Any, bind: bool = False):
        self.func = func
        self.name = name
        self.app = app
        self.bind = bind
    
    def delay(self, *args, **kwargs) -> AsyncResult:
        return self.apply_async(args=args, kwargs=kwargs)
    
    def apply_async(self, args: Tuple = (), kwargs: Optional[Dict] = None, **options) -> AsyncResult:
        if kwargs is None:
            kwargs = {}
        
        task_id = str(uuid.uuid4())
        
        if self.app.conf.task_always_eager:
            try:
                if self.bind:
                    result = self.func(self, *args, **kwargs)
                else:
                    result = self.func(*args, **kwargs)
                self.app._backend.set_result(task_id, result, "SUCCESS")
                return AsyncResult(task_id, app=self.app, result=result, state="SUCCESS")
            except Exception as e:
                self.app._backend.set_result(task_id, str(e), "FAILURE")
                return AsyncResult(task_id, app=self.app, result=str(e), state="FAILURE")
        
        self.app._broker.put_message(task_id, self.name, args, kwargs)
        return AsyncResult(task_id, app=self.app)
    
    def __call__(self, *args, **kwargs) -> Any:
        if self.bind:
            return self.func(self, *args, **kwargs)
        return self.func(*args, **kwargs)