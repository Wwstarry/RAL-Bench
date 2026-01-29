from typing import Any, Optional
import time


class AsyncResult:
    def __init__(self, task_id: str, app: Any, result: Any = None, state: str = "PENDING"):
        self.task_id = task_id
        self.id = task_id
        self.app = app
        self._result = result
        self._state = state
    
    def get(self, timeout: Optional[float] = None, propagate: bool = True) -> Any:
        start_time = time.time()
        
        while True:
            state, result = self.app._backend.get_result(self.task_id)
            
            if state == "SUCCESS":
                return result
            elif state == "FAILURE":
                if propagate:
                    raise Exception(result)
                return result
            elif state == "PENDING":
                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        raise TimeoutError(f"Task {self.task_id} did not complete within {timeout} seconds")
                time.sleep(0.01)
            else:
                time.sleep(0.01)
    
    def successful(self) -> bool:
        state, _ = self.app._backend.get_result(self.task_id)
        return state == "SUCCESS"
    
    def failed(self) -> bool:
        state, _ = self.app._backend.get_result(self.task_id)
        return state == "FAILURE"
    
    def ready(self) -> bool:
        state, _ = self.app._backend.get_result(self.task_id)
        return state in ("SUCCESS", "FAILURE")
    
    @property
    def state(self) -> str:
        if self._state != "PENDING":
            return self._state
        state, _ = self.app._backend.get_result(self.task_id)
        return state
    
    @property
    def result(self) -> Any:
        if self._result is not None:
            return self._result
        _, result = self.app._backend.get_result(self.task_id)
        return result