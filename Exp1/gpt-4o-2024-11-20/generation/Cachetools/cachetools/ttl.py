# TTLCache implementation

import time
from .cache import Cache

class TTLCache(Cache):
    """Time-To-Live (TTL) cache implementation."""

    def __init__(self, maxsize, ttl):
        super().__init__(maxsize)
        self.ttl = ttl
        self._store = {}
        self._timestamps = {}

    def __getitem__(self, key):
        if key not in self._store or self._is_expired(key):
            raise KeyError(key)
        return self._store[key]

    def __setitem__(self, key, value):
        if len(self._store) >= self.maxsize:
            self.evict()
        self._store[key] = value
        self._timestamps[key] = time.time()

    def __delitem__(self, key):
        del self._store[key]
        del self._timestamps[key]

    def evict(self):
        expired_keys = [key for key in self._store if self._is_expired(key)]
        for key in expired_keys:
            del self[key]
        if len(self._store) >= self.maxsize:
            oldest_key = min(self._timestamps, key=self._timestamps.get)
            del self[oldest_key]

    def _is_expired(self, key):
        return time.time() - self._timestamps[key] > self.ttl

    def __contains__(self, key):
        return key in self._store and not self._is_expired(key)

    def __iter__(self):
        return (key for key in self._store if not self._is_expired(key))

    def items(self):
        return {key: self._store[key] for key in self if not self._is_expired(key)}.items()