"""
cachetools - A simple caching library that provides the core API:
    Cache, LRUCache, TTLCache
    cached, cachedmethod
    keys (hashkey, methodkey)
"""

__version__ = '0.0.1'

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