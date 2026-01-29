class AsyncResult:
    """Task result encapsulating state and return value of a task."""
    
    def __init__(self, id, backend=None):
        self.id = id
        self.backend = backend
        
    def get(self, timeout=None, propagate=True, interval=0.5):
        """Get the result of the task, waiting if necessary."""
        return self.backend.get_result(self.id, timeout, propagate)
    
    def wait(self, timeout=None, propagate=True, interval=0.5):
        """Wait until task is ready, and return its result."""
        return self.get(timeout=timeout, propagate=propagate, interval=interval)
    
    def ready(self):
        """Return True if the task has been executed."""
        return self.backend.has_result(self.id)
    
    def successful(self):
        """Return True if the task executed successfully."""
        return self.state == 'SUCCESS'
    
    def failed(self):
        """Return True if the task failed."""
        return self.state == 'FAILURE'
    
    @property
    def state(self):
        """Return the current state of the task."""
        return self.backend.get_status(self.id)
    
    @property
    def status(self):
        """Alias for state."""
        return self.state
    
    @property
    def result(self):
        """Get the result (without raising exceptions)."""
        return self.backend.get_result(self.id, propagate=False)