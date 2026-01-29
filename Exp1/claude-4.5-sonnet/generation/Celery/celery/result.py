"""
Task result classes
"""

import time
from typing import Any, Optional


class AsyncResult:
    """Represents the result of a task"""
    
    def __init__(self, task_id: str, app=None):
        self.id = task_id
        self.task_id = task_id
        self.app = app
    
    def get(self, timeout=None, propagate=True, interval=0.5):
        """Wait for task completion and return result"""
        if timeout is not None:
            end_time = time.time() + timeout
        else:
            end_time = None
        
        while True:
            state, result = self.app.backend.get_result(self.task_id)
            
            if state == 'SUCCESS':
                return result
            elif state == 'FAILURE':
                if propagate:
                    if isinstance(result, Exception):
                        raise result
                    else:
                        raise Exception(str(result))
                return result
            elif state in ('PENDING', 'STARTED', 'RETRY'):
                # Task not ready yet
                if end_time is not None and time.time() >= end_time:
                    raise TimeoutError(f'Task {self.task_id} did not complete within {timeout}s')
                time.sleep(interval)
            else:
                # Unknown state
                if end_time is not None and time.time() >= end_time:
                    raise TimeoutError(f'Task {self.task_id} did not complete within {timeout}s')
                time.sleep(interval)
    
    def ready(self):
        """Check if task has completed"""
        state, _ = self.app.backend.get_result(self.task_id)
        return state in ('SUCCESS', 'FAILURE')
    
    def successful(self):
        """Check if task completed successfully"""
        state, _ = self.app.backend.get_result(self.task_id)
        return state == 'SUCCESS'
    
    def failed(self):
        """Check if task failed"""
        state, _ = self.app.backend.get_result(self.task_id)
        return state == 'FAILURE'
    
    @property
    def state(self):
        """Get task state"""
        state, _ = self.app.backend.get_result(self.task_id)
        return state
    
    @property
    def status(self):
        """Alias for state"""
        return self.state
    
    @property
    def result(self):
        """Get result without waiting"""
        _, result = self.app.backend.get_result(self.task_id)
        return result
    
    def __repr__(self):
        return f'<AsyncResult: {self.task_id}>'