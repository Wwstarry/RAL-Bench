"""
Minimal Celery-compatible distributed task queue library.
"""
from celery.app import Celery
from celery.result import AsyncResult
from celery.exceptions import (
    TaskRevokedError,
    TimeoutError,
    Retry,
    Ignore,
    Reject,
    MaxRetriesExceededError,
)

__version__ = "1.0.0"
__all__ = [
    "Celery",
    "AsyncResult",
    "TaskRevokedError",
    "TimeoutError",
    "Retry",
    "Ignore",
    "Reject",
    "MaxRetriesExceededError",
]