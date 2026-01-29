"""
Base backend class
"""

from typing import Any, Tuple


class BaseBackend:
    """Base class for result backends"""
    
    def store_result(self, task_id: str, result: Any, state: str):
        """Store task result"""
        raise NotImplementedError()
    
    def get_result(self, task_id: str) -> Tuple[str, Any]:
        """Get task result, returns (state, result)"""
        raise NotImplementedError()
    
    def forget(self, task_id: str):
        """Remove task result"""
        raise NotImplementedError()