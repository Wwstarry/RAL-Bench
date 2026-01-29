"""
TTL (Time To Live) cache implementation
"""

import time
import collections
from typing import Any, Callable, Optional, Tuple

from .cache import Cache


class TTLCache(Cache):
    """TTL cache with time-based expiration"""
    
    def __init__(self, maxsize: int, ttl: float, 
                 timer: Callable[[], float] = time.monotonic,
                 getsizeof: Optional[Callable[[Any], int]] = None):
        """
        Initialize TTL cache.
        
        Args:
            maxsize: Maximum number of items in cache
            ttl: Time to live in seconds
            timer: Function returning current time (default: time.monotonic)
            getsizeof: Function to calculate size of values (default: constant 1)
        """
        super().__init__(maxsize, getsizeof)
        self.ttl = ttl
        self.timer = timer
        self._expire_times = {}
        self._order = collections.OrderedDict()
    
    def __getitem__(self, key):
        """Get item if not expired"""
        self._expire()
        if key not in self._cache:
            raise KeyError(key)
        
        value = self._cache[key]
        # Update access time for LRU ordering
        self._order.move_to_end(key)
        return value
    
    def __setitem__(self, key, value):
        """Set item with expiration time"""
        self._expire()
        size = self.getsizeof(value)
        if size > self.maxsize:
            raise ValueError("value too large")
        
        if key in self._cache:
            self._size -= self.getsizeof(self._cache[key])
        
        self._cache[key] = value
        self._expire_times[key] = self.timer() + self.ttl
        self._order[key] = None
        self._size += size
        
        # Evict if necessary
        while self._size > self.maxsize:
            self.popitem()
    
    def __delitem__(self, key):
        """Delete item from cache"""
        value = self._cache[key]
        self._size -= self.getsizeof(value)
        del self._cache[key]
        del self._expire_times[key]
        del self._order[key]
    
    def __contains__(self, key):
        """Check if key is in cache and not expired"""
        self._expire()
        return key in self._cache
    
    def __iter__(self):
        """Iterate over non-expired cache keys"""
        self._expire()
        return iter(self._order)
    
    def __len__(self):
        """Number of non-expired items in cache"""
        self._expire()
        return len(self._cache)
    
    def __repr__(self):
        """String representation of cache"""
        self._expire()
        items = list(self._order.keys())
        return f"{self.__class__.__name__}({items!r}, maxsize={self.maxsize}, ttl={self.ttl})"
    
    def popitem(self):
        """Remove and return the least recently used non-expired item"""
        self._expire()
        if not self._order:
            raise KeyError("cache is empty")
        
        key = next(iter(self._order))
        value = self._cache[key]
        del self[key]
        return key, value
    
    def clear(self):
        """Clear all items from cache"""
        super().clear()
        self._expire_times.clear()
        self._order.clear()
    
    def get(self, key, default=None):
        """Get item from cache or return default if not found or expired"""
        try:
            return self[key]
        except KeyError:
            return default
    
    def pop(self, key, default=None):
        """Remove and return item from cache if not expired"""
        try:
            value = self[key]
            del self[key]
            return value
        except KeyError:
            return default
    
    def setdefault(self, key, default=None):
        """Get item from cache or set default if not found or expired"""
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default
    
    def _expire(self):
        """Remove expired items from cache"""
        now = self.timer()
        expired = []
        
        for key in list(self._order.keys()):
            if self._expire_times[key] < now:
                expired.append(key)
            else:
                # Items are in order, so we can stop at first non-expired
                break
        
        for key in expired:
            del self[key]