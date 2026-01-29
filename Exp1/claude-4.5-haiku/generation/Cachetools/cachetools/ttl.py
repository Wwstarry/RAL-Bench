"""Time-To-Live (TTL) cache implementation."""

import time
from cachetools.cache import Cache


class TTLCache(Cache):
    """Time-To-Live (TTL) cache implementation.
    
    Cache entries automatically expire after the specified TTL (in seconds).
    """

    def __init__(self, maxsize, ttl):
        """Initialize TTL cache with maximum size and time-to-live.
        
        Args:
            maxsize: Maximum number of items to store in the cache.
            ttl: Time-to-live for cache entries in seconds.
        """
        super().__init__(maxsize)
        self.__ttl = ttl
        self.__times = {}

    def __setitem__(self, key, value):
        """Set an item in the cache with current timestamp."""
        self.__expire()
        maxsize = self.maxsize
        if maxsize is None or maxsize <= 0:
            raise ValueError('maxsize must be a positive integer or None')
        
        if key not in self.__times and len(self.__times) >= maxsize:
            self.popitem()
        
        super().__setitem__(key, value)
        self.__times[key] = time.time()

    def __getitem__(self, key):
        """Get an item from the cache, checking if it has expired."""
        self.__expire()
        if key not in self.__times:
            raise KeyError(key)
        return super().__getitem__(key)

    def __delitem__(self, key):
        """Delete an item from the cache."""
        super().__delitem__(key)
        del self.__times[key]

    def __contains__(self, key):
        """Check if a key is in the cache and not expired."""
        self.__expire()
        return key in self.__times

    def __iter__(self):
        """Iterate over non-expired cache keys."""
        self.__expire()
        return iter(self.__times)

    def __len__(self):
        """Return the number of non-expired items in the cache."""
        self.__expire()
        return len(self.__times)

    def popitem(self):
        """Remove and return an arbitrary non-expired (key, value) pair."""
        self.__expire()
        if not self.__times:
            raise KeyError('popitem(): cache is empty')
        key = next(iter(self.__times))
        value = super().__getitem__(key)
        del self[key]
        return key, value

    def __expire(self):
        """Remove all expired entries from the cache."""
        now = time.time()
        expired_keys = [
            key for key, timestamp in self.__times.items()
            if now - timestamp > self.__ttl
        ]
        for key in expired_keys:
            del self[key]

    @property
    def ttl(self):
        """Return the time-to-live for cache entries."""
        return self.__ttl

    def __repr__(self):
        """Return string representation of the TTL cache."""
        self.__expire()
        items = {k: super().__getitem__(k) for k in self.__times}
        return f'{self.__class__.__name__}({items!r}, maxsize={self.maxsize}, ttl={self.__ttl})'