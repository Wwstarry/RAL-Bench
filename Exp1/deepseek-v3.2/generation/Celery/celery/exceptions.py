"""
Celery exceptions.
"""


class CeleryError(Exception):
    """Base Celery error."""
    pass


class TimeoutError(CeleryError):
    """Operation timed out."""
    pass


class TaskRevokedError(CeleryError):
    """Task was revoked."""
    pass


class NotConfigured(CeleryError):
    """Celery not configured."""
    pass


class ImproperlyConfigured(CeleryError):
    """Celery improperly configured."""
    pass


class SecurityError(CeleryError):
    """Security related error."""
    pass


class MaxRetriesExceededError(CeleryError):
    """Task max retries exceeded."""
    pass


class Retry(CeleryError):
    """Task retry exception."""
    pass


class Ignore(CeleryError):
    """Task ignore exception."""
    pass


class Reject(CeleryError):
    """Task reject exception."""
    pass