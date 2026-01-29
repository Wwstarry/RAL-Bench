"""
Minimal pure-Python Celery-compatible API surface for the unit tests.

This is NOT the real Celery project. It implements a tiny subset of the
public API: Celery application, task decorator/registry, eager/in-memory
execution, and AsyncResult-like results.
"""

from __future__ import annotations

from .app.base import Celery
from .local import current_app
from .app.base import shared_task

__all__ = ["Celery", "shared_task", "current_app"]

__version__ = "0.0.0-test"