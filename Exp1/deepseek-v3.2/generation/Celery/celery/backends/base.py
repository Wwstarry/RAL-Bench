"""
Base backend classes.
"""

from ..exceptions import TimeoutError


class BaseBackend:
    """Base result backend."""
    
    def __init__(self, app, url=None, **kwargs):
        self.app = app
    
    def encode_result(self, result, status):
        """Encode result for storage."""
        return result, status
    
    def decode_result(self, payload):
        """Decode stored result."""
        return payload
    
    def store_result(self, task_id, result, state, **kwargs):
        """Store task result."""
        pass
    
    def get_result(self, task_id):
        """Get task result."""
        pass
    
    def wait_for(self, task_id, timeout=None, propagate=True):
        """Wait for task result."""
        pass
    
    def get_status(self, task_id):
        """Get task status."""
        pass