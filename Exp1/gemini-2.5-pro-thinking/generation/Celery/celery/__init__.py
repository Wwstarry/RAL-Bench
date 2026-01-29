__version__ = "5.2.7"
__author__ = "Ask Solem"
__contact__ = "ask@celeryproject.org"
__homepage__ = "https://celeryproject.org"
__docformat__ = "restructuredtext"

from .app.base import Celery
from .result import AsyncResult
from .exceptions import TimeoutError

# A minimal placeholder for shared_task if needed by tests.
def shared_task(*args, **opts):
    """
    Decorator to create a task that is not bound to a specific app instance.
    Note: This is a simplified implementation for API compatibility.
    The created task must be discovered by a Celery app instance to be used.
    """
    def decorator(func):
        from .app.task import Task
        # In this simplified version, the task is created but not bound.
        # It will be bound when an app discovers and registers it.
        # For the purpose of this library, tasks are always registered
        # via @app.task, so this is mostly for API signature compatibility.
        return Task(func, app=None, **opts)

    if len(args) == 1 and callable(args[0]):
        return decorator(args[0])
    return decorator