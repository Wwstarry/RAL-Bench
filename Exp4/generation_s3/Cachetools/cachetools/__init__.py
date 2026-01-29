"""
A small, pure-Python subset of the `cachetools` project.

This package implements the core APIs commonly used by downstream projects:
- Cache (base class)
- LRUCache
- TTLCache
- cached / cachedmethod decorators
- key helpers in cachetools.keys
"""

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

__version__ = "0.0.0"