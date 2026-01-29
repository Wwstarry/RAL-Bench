"""
Result backends.
"""


class BaseBackend:
    """Base result backend."""
    
    def __init__(self, app, url=None, **kwargs):
        self.app = app
    
    def store_result(self, task_id, result, state, **kwargs):
        """Store task result."""
        pass
    
    def get_result(self, task_id):
        """Get task result."""
        pass