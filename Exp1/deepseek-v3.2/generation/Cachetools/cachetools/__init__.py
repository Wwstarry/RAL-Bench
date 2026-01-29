"""
Cachetools - Python caching utilities
"""

from .cache import Cache
from .lru import LRUCache
from .ttl import TTLCache
from .decorators import cached, cachedmethod
from .keys import hashkey

__all__ = [
    'Cache',
    'LRUCache',
    'TTLCache',
    'cached',
    'cachedmethod',
    'hashkey',
]

__version__ = '1.0.0'