"""
A tiny, pure-Python subset of Celery's public API sufficient for local testing.

This is NOT the real Celery project.
"""
from __future__ import annotations

from .app.base import Celery

__all__ = ["Celery", "__version__"]

__version__ = "0.0.0-agent"