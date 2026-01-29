"""
Pure Python caching utility providing a subset of Cachetools-compatible API.

Public API:
- Cache, LRUCache, TTLCache base classes
- Decorators: cached, cachedmethod
- Key helpers: keys.hashkey and related functions

Modules provided:
- cachetools
- cachetools.cache
- cachetools.lru
- cachetools.ttl
- cachetools.keys
"""

from .cache import Cache
from .lru import LRUCache
from .ttl import TTLCache
from .decorators import cached, cachedmethod
from .keys import (
    hashkey,
    typedkey,
    methodkey,
    deepfreeze,
)

__all__ = [
    "Cache",
    "LRUCache",
    "TTLCache",
    "cached",
    "cachedmethod",
    "hashkey",
    "typedkey",
    "methodkey",
    "deepfreeze",
]