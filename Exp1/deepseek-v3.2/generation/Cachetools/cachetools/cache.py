"""
Base cache implementation
"""

from collections.abc import MutableMapping
from typing import Any, Callable, Optional


class Cache(MutableMapping):
    """Base cache class implementing MutableMapping interface"""
    
    def __init__(self, maxsize: int, getsizeof: Optional[Callable[[Any], int]] = None):
        """
        Initialize cache with maximum size.
        
        Args:
            maxsize: Maximum number of items in cache
            getsizeof: Function to calculate size of values (default: constant 1)
        """
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")
        
        self.maxsize = maxsize
        self.getsizeof = getsizeof or (lambda x: 1)
        self._cache = {}
        self._size = 0
    
    def __getitem__(self, key):
        """Get item from cache"""
        return self._cache[key]
    
    def __setitem__(self, key, value):
        """Set item in cache"""
        size = self.getsizeof(value)
        if size > self.maxsize:
            raise ValueError("value too large")
        
        if key in self._cache:
            self._size -= self.getsizeof(self._cache[key])
        
        self._cache[key] = value
        self._size += size
        
        # Evict if necessary
        while self._size > self.maxsize:
            self.popitem()
    
    def __delitem__(self, key):
        """Delete item from cache"""
        value = self._cache[key]
        self._size -= self.getsizeof(value)
        del self._cache[key]
    
    def __iter__(self):
        """Iterate over cache keys"""
        return iter(self._cache)
    
    def __len__(self):
        """Number of items in cache"""
        return len(self._cache)
    
    def __contains__(self, key):
        """Check if key is in cache"""
        return key in self._cache
    
    def __repr__(self):
        """String representation of cache"""
        return f"{self.__class__.__name__}({self._cache!r}, maxsize={self.maxsize})"
    
    def popitem(self):
        """Remove and return an item from the cache.
        
        Must be implemented by subclasses to define eviction policy.
        """
        raise NotImplementedError
    
    def clear(self):
        """Clear all items from cache"""
        self._cache.clear()
        self._size = 0
    
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