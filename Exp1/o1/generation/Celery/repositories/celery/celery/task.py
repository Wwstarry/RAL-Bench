"""
Minimal Celery-like Task implementation.
"""

import uuid
import traceback

from .result import AsyncResult
from . import states


class Task:
    """
    Minimal Celery-like Task class.
    """

    abstract = True
    ignore_result = False
    name = None
    app = None
    _bind = False

    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        """
        The actual task body. Overridden by user code.
        """
        raise NotImplementedError

    def apply_async(self, args=None, kwargs=None, **options):
        """
        Apply this task asynchronously and return a result handle.
        """
        args = args or ()
        kwargs = kwargs or {}

        # Generate a task id
        task_id = uuid.uuid4().hex
        # In a real system, we'd send to a broker here.
        # If eager, we run now:
        if self.app.conf.get("task_always_eager", True):
            try:
                result = self.run(*args, **kwargs) if not self._bind else self.run(self, *args, **kwargs)
                AsyncResult.store_result(task_id, result, state=states.SUCCESS, exc=None, tb=None)
            except Exception as exc:
                AsyncResult.store_result(task_id, None, state=states.FAILURE, exc=exc, tb=traceback.format_exc())
        else:
            # Non-eager path. We might queue the task or so. For this minimal version,
            # we won't actually queue but mimic a state change.
            AsyncResult.store_result(task_id, None, state=states.PENDING)

        return AsyncResult(task_id)

    def delay(self, *args, **kwargs):
        """
        Shortcut to apply_async with only args/kwargs.
        """
        return self.apply_async(args=args, kwargs=kwargs)