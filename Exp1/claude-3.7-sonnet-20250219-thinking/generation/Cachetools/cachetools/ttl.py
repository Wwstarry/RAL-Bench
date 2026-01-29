"""Time-To-Live (TTL) cache implementation."""

import time
from .lru import LRUCache


class TTLCache(LRUCache):
    """LRU Cache implementation with per-item time-to-live (TTL) value."""

    def __init__(self, maxsize, ttl, timer=time.monotonic, getsizeof=None):
        LRUCache.__init__(self, maxsize, getsizeof)
        self.timer = timer
        self.ttl = ttl
        self._expires = {}

    def __getitem__(self, key):
        value = LRUCache.__getitem__(self, key)
        if self._expires[key] < self.timer():
            del self[key]
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        expires = self.timer() + self.ttl
        if key in self:
            del self[key]
        LRUCache.__setitem__(self, key, value)
        self._expires[key] = expires

    def __delitem__(self, key):
        LRUCache.__delitem__(self, key)
        del self._expires[key]

    def __iter__(self):
        now = self.timer()
        for key in list(self._data):
            if self._expires[key] < now:
                del self[key]
            else:
                yield key

    def expire(self, time=None):
        """Remove expired items from the cache."""
        if time is None:
            time = self.timer()
        for key in list(self._data):
            if self._expires[key] < time:
                del self[key]
        return len(self)