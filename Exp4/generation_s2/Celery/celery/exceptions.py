class TimeoutError(Exception):
    """Raised by AsyncResult.get(timeout=...) when the result isn't ready."""


class ImproperlyConfigured(Exception):
    """Raised when the app is configured inconsistently."""


class TaskError(Exception):
    """Base class for task execution errors (wrapper around user exceptions)."""