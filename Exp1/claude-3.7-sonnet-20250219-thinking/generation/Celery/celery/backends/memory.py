from celery.backends.base import Backend
import time

class MemoryBackend(Backend):
    """In-memory result backend."""
    
    def __init__(self):
        self._results = {}
    
    def store_result(self, task_id, result, status):
        """Store a task result."""
        self._results[task_id] = {
            "result": result,
            "status": status,
            "traceback": None
        }
    
    def store_exception(self, task_id, exc):
        """Store a task exception."""
        self._results[task_id] = {
            "result": exc,
            "status": "FAILURE",
            "traceback": None
        }
    
    def get_result(self, task_id, timeout=None, propagate=True):
        """Get a task result."""
        if timeout:
            end_time = time.time() + timeout
            while time.time() < end_time:
                if task_id in self._results:
                    break
                time.sleep(0.1)
            else:
                raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")
        
        if task_id not in self._results:
            return None
        
        result_data = self._results[task_id]
        
        if result_data["status"] == "FAILURE" and propagate:
            if isinstance(result_data["result"], Exception):
                raise result_data["result"]
            raise Exception(str(result_data["result"]))
        
        return result_data["result"]
    
    def get_status(self, task_id):
        """Get the status of a task."""
        return self._results.get(task_id, {}).get("status")
    
    def has_result(self, task_id):
        """Check if a task has a result."""
        return task_id in self._results