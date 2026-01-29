class BaseBackend:
    """Abstract base class for result backends."""

    def store_result(self, task_id, result, state, traceback=None):
        """Store the result of a task."""
        raise NotImplementedError("subclass responsibility")

    def get_result(self, task_id):
        """Get the result of a task."""
        raise NotImplementedError("subclass responsibility")

    def get_state(self, task_id):
        """Get the state of a task."""
        raise NotImplementedError("subclass responsibility")

    def forget(self, task_id):
        """Forget a task result."""
        pass  # Default is a no-op