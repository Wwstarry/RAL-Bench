"""Extensible memoizing collections and decorators"""

from .cache import Cache
from .decorators import cached, cachedmethod
from .lru import LRUCache
from .ttl import TTLCache

__all__ = ['Cache', 'LRUCache', 'TTLCache', 'cached', 'cachedmethod']