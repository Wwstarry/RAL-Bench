import time
from collections import OrderedDict
from .cache import Cache

class TTLCache(Cache):
    """Cache with time-to-live eviction."""

    def __init__(self, maxsize, ttl, timer=time.monotonic, missing=None):
        if maxsize is None or maxsize <= 0:
            raise ValueError("maxsize should be a positive integer")
        if ttl <= 0:
            raise ValueError("ttl should be a positive number")
        super().__init__(maxsize=maxsize, missing=missing)
        self.ttl = ttl
        self.timer = timer
        self._Cache__data = OrderedDict()
        self._expire_times = dict()

    def __getitem__(self, key):
        now = self.timer()
        try:
            expire = self._expire_times[key]
            if expire <= now:
                # expired
                self.__delitem__(key)
                raise KeyError(key)
            # update recency
            value = self._Cache__data.pop(key)
            self._Cache__data[key] = value
            self._expire_times[key] = expire
            return value
        except KeyError:
            if self._Cache__missing is not None:
                value = self._Cache__missing(key)
                self[key] = value
                return value
            raise

    def __setitem__(self, key, value):
        now = self.timer()
        expire = now + self.ttl
        if key in self._Cache__data:
            self._Cache__data.pop(key)
        self._Cache__data[key] = value
        self._expire_times[key] = expire
        self._evict()

    def __delitem__(self, key):
        del self._Cache__data[key]
        del self._expire_times[key]

    def __contains__(self, key):
        now = self.timer()
        expire = self._expire_times.get(key)
        if expire is None:
            return False
        if expire <= now:
            # expired
            self.__delitem__(key)
            return False
        return key in self._Cache__data

    def __len__(self):
        self.expire()
        return len(self._Cache__data)

    def __iter__(self):
        self.expire()
        return iter(self._Cache__data)

    def clear(self):
        self._Cache__data.clear()
        self._expire_times.clear()

    def pop(self, key, default=None):
        self.expire()
        if default is None:
            value = self._Cache__data.pop(key)
            del self._expire_times[key]
            return value
        else:
            value = self._Cache__data.pop(key, default)
            self._expire_times.pop(key, None)
            return value

    def popitem(self):
        self.expire()
        key, value = self._Cache__data.popitem(last=False)
        del self._expire_times[key]
        return key, value

    def expire(self):
        """Remove expired items."""
        now = self.timer()
        keys_to_remove = [key for key, expire in self._expire_times.items() if expire <= now]
        for key in keys_to_remove:
            self.__delitem__(key)

    def _evict(self):
        self.expire()
        while self.maxsize is not None and len(self._Cache__data) > self.maxsize:
            key, _ = self._Cache__data.popitem(last=False)
            del self._expire_times[key]