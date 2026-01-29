"""
Celery exceptions
"""


class CeleryError(Exception):
    """Base exception for Celery"""
    pass


class TaskRevokedError(CeleryError):
    """Task was revoked"""
    pass


class TimeoutError(CeleryError):
    """Task timeout"""
    pass


class Retry(CeleryError):
    """Task retry exception"""
    pass


class Reject(CeleryError):
    """Task reject exception"""
    pass


class Ignore(CeleryError):
    """Task ignore exception"""
    pass