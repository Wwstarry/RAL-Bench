"""
Pure-Python subset of the cachetools API.

This package is intended to be API-compatible with the core parts of the
reference "cachetools" project that are commonly used by test suites.

Modules provided:
- cachetools.cache
- cachetools.lru
- cachetools.ttl
- cachetools.keys
- cachetools.decorators
"""

from .cache import Cache
from .lru import LRUCache
from .ttl import TTLCache
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