"""
A small, pure-Python subset of the cachetools project API.

This package is intentionally minimal but aims to be compatible with the core
parts commonly used by black-box tests: Cache, LRUCache, TTLCache, cached,
cachedmethod, and key helper functions in cachetools.keys.
"""

from .cache import Cache
from .lru import LRUCache
from .ttl import TTLCache
from .decorators import cached, cachedmethod
from . import keys
from .keys import hashkey, typedkey, methodkey, typedmethodkey

__all__ = [
    "Cache",
    "LRUCache",
    "TTLCache",
    "cached",
    "cachedmethod",
    "keys",
    "hashkey",
    "typedkey",
    "methodkey",
    "typedmethodkey",
]

__version__ = "0.0.0"