# LRUCache implementation

from collections import OrderedDict
from .cache import Cache

class LRUCache(Cache):
    """Least-Recently-Used (LRU) cache implementation."""

    def __init__(self, maxsize):
        super().__init__(maxsize)
        self._store = OrderedDict()

    def __getitem__(self, key):
        value = self._store.pop(key)
        self._store[key] = value  # Update access order
        return value

    def __setitem__(self, key, value):
        if key in self._store:
            self._store.pop(key)
        elif len(self._store) >= self.maxsize:
            self.evict()
        self._store[key] = value

    def __delitem__(self, key):
        del self._store[key]

    def evict(self):
        self._store.popitem(last=False)  # Remove least recently used item

    def __contains__(self, key):
        return key in self._store

    def __iter__(self):
        return iter(self._store)

    def items(self):
        return self._store.items()