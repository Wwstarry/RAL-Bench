"""Extensible memoizing collections and decorators"""

from .cache import Cache, LRUCache, TTLCache
from .decorators import cached, cachedmethod
from . import keys

__all__ = (
    'Cache',
    'LRUCache',
    'TTLCache',
    'cached',
    'cachedmethod',
    'keys',
)

__version__ = '5.0.0'  # Mock version for compatibility