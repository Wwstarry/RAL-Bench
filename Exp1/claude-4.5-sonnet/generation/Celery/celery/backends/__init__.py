"""
Result backends
"""

from celery.backends.base import BaseBackend
from celery.backends.memory import MemoryBackend

__all__ = ['BaseBackend', 'MemoryBackend']