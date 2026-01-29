"""
A small, pure-Python subset of the `cachetools` project.

This package implements the core API surface commonly used by test suites:
- Cache, LRUCache, TTLCache
- cached, cachedmethod
- key functions in cachetools.keys
"""
from __future__ import annotations

from .cache import Cache, LRUCache, TTLCache
from .decorators import cached, cachedmethod
from . import keys

__all__ = [
    "Cache",
    "LRUCache",
    "TTLCache",
    "cached",
    "cachedmethod",
    "keys",
]