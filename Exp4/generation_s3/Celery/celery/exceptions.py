from __future__ import annotations


class CeleryError(Exception):
    """Base exception class."""


class TimeoutError(CeleryError):
    """Raised by AsyncResult.get on timeout."""


class ImproperlyConfigured(CeleryError):
    """Raised when configuration is invalid for requested operation."""


class TaskRevokedError(CeleryError):
    """Stub for API compatibility."""