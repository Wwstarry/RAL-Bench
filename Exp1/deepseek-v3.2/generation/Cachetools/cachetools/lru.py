"""
LRU (Least Recently Used) cache implementation
"""

import collections
from typing import Any, Callable, Optional

from .cache import Cache


class LRUCache(Cache):
    """LRU cache with least-recently-used eviction policy"""
    
    def __init__(self, maxsize: int, getsizeof: Optional[Callable[[Any], int]] = None):
        super().__init__(maxsize, getsizeof)
        self._order = collections.OrderedDict()
    
    def __getitem__(self, key):
        """Get item and mark as recently used"""
        value = self._cache[key]
        # Move to end (most recently used)
        self._order.move_to_end(key)
        return value
    
    def __setitem__(self, key, value):
        """Set item and mark as recently used"""
        size = self.getsizeof(value)
        if size > self.maxsize:
            raise ValueError("value too large")
        
        if key in self._cache:
            self._size -= self.getsizeof(self._cache[key])
        
        self._cache[key] = value
        self._order[key] = None  # Value doesn't matter, we just track order
        self._size += size
        
        # Evict if necessary
        while self._size > self.maxsize:
            self.popitem()
    
    def __delitem__(self, key):
        """Delete item from cache"""
        value = self._cache[key]
        self._size -= self.getsizeof(value)
        del self._cache[key]
        del self._order[key]
    
    def __contains__(self, key):
        """Check if key is in cache"""
        return key in self._cache
    
    def __iter__(self):
        """Iterate over cache keys in LRU order (least recently used first)"""
        return iter(self._order)
    
    def __len__(self):
        """Number of items in cache"""
        return len(self._cache)
    
    def __repr__(self):
        """String representation of cache"""
        items = list(self._order.keys())
        return f"{self.__class__.__name__}({items!r}, maxsize={self.maxsize})"
    
    def popitem(self):
        """Remove and return the least recently used item"""
        if not self._order:
            raise KeyError("cache is empty")
        
        key = next(iter(self._order))
        value = self._cache[key]
        del self[key]
        return key, value
    
    def clear(self):
        """Clear all items from cache"""
        super().clear()
        self._order.clear()
    
    def get(self, key, default=None):
        """Get item from cache or return default if not found"""
        try:
            return self[key]
        except KeyError:
            return default
    
    def pop(self, key, default=None):
        """Remove and return item from cache"""
        try:
            value = self[key]
            del self[key]
            return value
        except KeyError:
            return default
    
    def setdefault(self, key, default=None):
        """Get item from cache or set default if not found"""
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default