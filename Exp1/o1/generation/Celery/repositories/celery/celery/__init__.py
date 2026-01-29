"""
Minimal Celery-compatible package initialization.
"""

__version__ = "0.0.1"

from .app import Celery

__all__ = ["Celery", "__version__"]