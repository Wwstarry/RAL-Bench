"""A caching library with multiple cache implementations."""

from cachetools.cache import Cache
from cachetools.lru import LRUCache
from cachetools.ttl import TTLCache
from cachetools.decorators import cached, cachedmethod
from cachetools import keys

__all__ = [
    'Cache',
    'LRUCache',
    'TTLCache',
    'cached',
    'cachedmethod',
    'keys',
]

__version__ = '5.3.0'