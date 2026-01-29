# Minimal Celery-compatible API surface

from .app import Celery, Task, AsyncResult

__all__ = ["Celery", "Task", "AsyncResult"]

__version__ = "0.1.0"

# Common state constants
PENDING = "PENDING"
STARTED = "STARTED"
SUCCESS = "SUCCESS"
FAILURE = "FAILURE"
RETRY = "RETRY"