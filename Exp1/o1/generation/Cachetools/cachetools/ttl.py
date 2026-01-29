import time
from collections import OrderedDict
from .cache import Cache

class TTLCache(Cache):
    """
    Time-to-live cache implementation. Entries expire after
    ttl seconds. Expired items are evicted automatically on access.
    """

    def __init__(self, maxsize=128, ttl=300):
        super().__init__(maxsize)
        self.ttl = ttl
        self._store = OrderedDict()

    def __getitem__(self, key):
        self._expire()
        value, expires_at = self._store[key]
        if time.time() >= expires_at:
            del self._store[key]
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        self._expire()
        expires_at = time.time() + self.ttl
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = (value, expires_at)
        self._check_size()

    def _check_size(self):
        if self.maxsize is not None:
            while len(self._store) > self.maxsize:
                self._store.popitem(last=False)

    def _expire(self):
        """Evict all expired entries."""
        now = time.time()
        expired_keys = []
        for key, (val, expires_at) in self._store.items():
            if now >= expires_at:
                expired_keys.append(key)
        for key in expired_keys:
            del self._store[key]