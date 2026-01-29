"""Celery exceptions"""

class CeleryError(Exception):
    """Base Celery exception"""

class TaskError(CeleryError):
    """Task related errors"""

class TimeoutError(CeleryError):
    """Operation timed out"""

class Retry(TaskError):
    """Task retry exception"""
    
    def __init__(self, message=None, **kwargs):
        super().__init__(message or 'Task retry')
        self.kwargs = kwargs

class Reject(TaskError):
    """Task reject exception"""
    
    def __init__(self, message=None, **kwargs):
        super().__init__(message or 'Task rejected')
        self.kwargs = kwargs

class Ignore(TaskError):
    """Task ignore exception"""

class MaxRetriesExceededError(TaskError):
    """Task max retries exceeded"""

class SoftTimeLimitExceeded(TaskError):
    """Task soft time limit exceeded"""

class TimeLimitExceeded(TaskError):
    """Task time limit exceeded"""