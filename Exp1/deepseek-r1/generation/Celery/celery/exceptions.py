"""
Celery-compatible exceptions.
"""

class TaskRevokedError(Exception):
    """Task was revoked."""
    pass

class TimeoutError(Exception):
    """Operation timed out."""
    pass

class Retry(Exception):
    """Task should be retried."""
    def __init__(self, message=None, *args, **kwargs):
        super().__init__(message or "Task should be retried")

class Ignore(Exception):
    """Task should be ignored."""
    pass

class Reject(Exception):
    """Task should be rejected."""
    pass

class MaxRetriesExceededError(Exception):
    """Maximum retries exceeded."""
    pass