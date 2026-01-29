class Backend:
    """Base class for result backends."""
    
    def store_result(self, task_id, result, status):
        """Store a task result."""
        raise NotImplementedError()
    
    def store_exception(self, task_id, exc):
        """Store a task exception."""
        raise NotImplementedError()
    
    def get_result(self, task_id, timeout=None, propagate=True):
        """Get a task result."""
        raise NotImplementedError()
    
    def get_status(self, task_id):
        """Get the status of a task."""
        raise NotImplementedError()
    
    def has_result(self, task_id):
        """Check if a task has a result."""
        raise NotImplementedError()