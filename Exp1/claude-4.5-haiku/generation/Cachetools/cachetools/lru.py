"""Least Recently Used (LRU) cache implementation."""

from collections import OrderedDict
from cachetools.cache import Cache


class LRUCache(Cache):
    """Least Recently Used (LRU) cache implementation.
    
    Items are evicted based on least recent access (get or set).
    """

    def __init__(self, maxsize):
        """Initialize LRU cache with maximum size.
        
        Args:
            maxsize: Maximum number of items to store in the cache.
        """
        super().__init__(maxsize)
        self.__order = OrderedDict()

    def __setitem__(self, key, value):
        """Set an item in the cache, updating access order."""
        maxsize = self.maxsize
        if maxsize is None or maxsize <= 0:
            raise ValueError('maxsize must be a positive integer or None')
        
        # If key exists, remove it from order tracking
        if key in self.__order:
            del self.__order[key]
        # If we're at capacity and adding a new key, evict the least recently used
        elif len(self.__order) >= maxsize:
            # Remove the first (oldest) item
            lru_key = next(iter(self.__order))
            del self[lru_key]
        
        # Add/update the item
        super().__setitem__(key, value)
        self.__order[key] = None

    def __getitem__(self, key):
        """Get an item from the cache, updating access order."""
        value = super().__getitem__(key)
        # Move to end (most recently used)
        del self.__order[key]
        self.__order[key] = None
        return value

    def __delitem__(self, key):
        """Delete an item from the cache."""
        super().__delitem__(key)
        del self.__order[key]

    def popitem(self):
        """Remove and return the least recently used (key, value) pair."""
        # Get the first (least recently used) key
        key = next(iter(self.__order))
        value = super().__getitem__(key)
        del self[key]
        return key, value

    def __repr__(self):
        """Return string representation of the LRU cache."""
        items = {k: super().__getitem__(k) for k in self.__order}
        return f'{self.__class__.__name__}({items!r}, maxsize={self.maxsize})'