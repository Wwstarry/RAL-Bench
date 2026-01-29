"""
A tiny, pure-Python, Celery-like task queue implementation.

This repository is intentionally minimal and designed to satisfy a subset of
Celery's public API used by the test-suite for this kata.

Key features:
- celery.Celery app class
- @app.task decorator with name= and bind=
- Task.delay/apply_async returning an AsyncResult with get()/successful()/failed()
- In-memory "broker"/backend and eager execution mode
- app.send_task(name, args, kwargs)
"""

from .app.base import Celery  # noqa: F401
from .result import AsyncResult  # noqa: F401
from .states import PENDING, STARTED, SUCCESS, FAILURE, REVOKED, RETRY  # noqa: F401

__all__ = [
    "Celery",
    "AsyncResult",
    "PENDING",
    "STARTED",
    "SUCCESS",
    "FAILURE",
    "REVOKED",
    "RETRY",
]

__version__ = "0.1.0"