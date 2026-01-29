class CeleryError(Exception):
    """Base class for all Celery errors."""
    pass

class TaskError(CeleryError):
    """Task related errors."""
    pass

class TimeoutError(TaskError):
    """Task timed out."""
    pass