import time
from collections import OrderedDict
from .cache import Cache

class TTLCache(Cache):
    """Cache implementation with per-item time-to-live (TTL) expiration."""

    def __init__(self, maxsize, ttl, timer=time.monotonic, missing=None, getsizeof=None):
        if ttl <= 0:
            raise ValueError("ttl must be > 0")
        super().__init__(maxsize, missing, getsizeof)
        self.ttl = ttl
        self.timer = timer
        self._Cache__data = OrderedDict()

    def __getitem__(self, key):
        now = self.timer()
        try:
            value, expires = self._Cache__data[key]
            if expires <= now:
                del self._Cache__data[key]
                raise KeyError(key)
            # Move to end to mark as recently used
            self._Cache__data.move_to_end(key)
            return value
        except KeyError:
            if self.missing is not None:
                return self.missing(self, key)
            raise

    def __setitem__(self, key, value):
        now = self.timer()
        expires = now + self.ttl
        data = self._Cache__data
        if key in data:
            del data[key]
        data[key] = (value, expires)
        self._evict(now)

    def __delitem__(self, key):
        del self._Cache__data[key]

    def __contains__(self, key):
        try:
            value, expires = self._Cache__data[key]
            if expires <= self.timer():
                del self._Cache__data[key]
                return False
            return True
        except KeyError:
            return False

    def __len__(self):
        self._evict(self.timer())
        return len(self._Cache__data)

    def __iter__(self):
        now = self.timer()
        keys = list(self._Cache__data.keys())
        for key in keys:
            try:
                value, expires = self._Cache__data[key]
                if expires > now:
                    yield key
                else:
                    del self._Cache__data[key]
            except KeyError:
                continue

    def clear(self):
        self._Cache__data.clear()

    def popitem(self):
        now = self.timer()
        self._evict(now)
        while self._Cache__data:
            key, (value, expires) = self._Cache__data.popitem(last=False)
            if expires > now:
                return key, value
        raise KeyError("popitem(): cache is empty")

    def _evict(self, now):
        # Remove expired items
        data = self._Cache__data
        keys = list(data.keys())
        for key in keys:
            value, expires = data[key]
            if expires <= now:
                del data[key]
        # Enforce maxsize
        while self.maxsize is not None and len(data) > self.maxsize:
            data.popitem(last=False)