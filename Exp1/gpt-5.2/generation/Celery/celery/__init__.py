"""
A tiny, pure-Python subset of Celery's public API suitable for local tests.

This is NOT the real Celery project. It implements a small compatible surface:
- celery.Celery
- @app.task decorator (name=..., bind=...)
- .delay/.apply_async returning AsyncResult with .get(), .successful(), .failed()
- app.send_task(name, args, kwargs)
- app.conf with eager options and broker/result backend placeholders
"""
from __future__ import annotations

from .app.base import Celery

__all__ = ["Celery"]
__version__ = "0.0.0"