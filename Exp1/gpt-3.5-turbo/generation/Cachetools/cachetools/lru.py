from collections import OrderedDict
from .cache import Cache

class LRUCache(Cache):
    """Least-recently-used cache implementation."""

    def __init__(self, maxsize, missing=None):
        if maxsize is None or maxsize <= 0:
            raise ValueError("maxsize should be a positive integer")
        super().__init__(maxsize=maxsize, missing=missing)
        self._Cache__data = OrderedDict()

    def __getitem__(self, key):
        try:
            value = self._Cache__data.pop(key)
            self._Cache__data[key] = value  # move to end (most recently used)
            return value
        except KeyError:
            if self._Cache__missing is not None:
                value = self._Cache__missing(key)
                self[key] = value
                return value
            raise

    def __setitem__(self, key, value):
        if key in self._Cache__data:
            self._Cache__data.pop(key)
        self._Cache__data[key] = value
        self._evict()

    def __delitem__(self, key):
        del self._Cache__data[key]

    def __contains__(self, key):
        return key in self._Cache__data

    def __len__(self):
        return len(self._Cache__data)

    def __iter__(self):
        return iter(self._Cache__data)

    def clear(self):
        self._Cache__data.clear()

    def pop(self, key, default=None):
        if default is None:
            return self._Cache__data.pop(key)
        else:
            return self._Cache__data.pop(key, default)

    def popitem(self):
        return self._Cache__data.popitem(last=False)

    def _evict(self):
        while self.maxsize is not None and len(self._Cache__data) > self.maxsize:
            self._Cache__data.popitem(last=False)