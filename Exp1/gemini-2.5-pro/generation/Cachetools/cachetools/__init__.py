"""Extensible memoizing collections and decorators"""

__version__ = '5.3.0'

from .cache import Cache, LRUCache, TTLCache
from .decorators import cached, cachedmethod
from .keys import hashkey, typedkey
from . import keys

__all__ = (
    'Cache',
    'LRUCache',
    'TTLCache',
    'cached',
    'cachedmethod',
    'hashkey',
    'typedkey',
    'keys'
)