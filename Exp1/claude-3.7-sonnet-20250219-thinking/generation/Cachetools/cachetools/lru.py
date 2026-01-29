"""Least Recently Used (LRU) cache implementation."""

import collections
from .cache import Cache


class LRUCache(Cache):
    """Least Recently Used (LRU) cache implementation."""

    def __init__(self, maxsize, getsizeof=None):
        Cache.__init__(self, maxsize, getsizeof)
        self._data = collections.OrderedDict()

    def __on_access__(self, key):
        """Move accessed item to the end of the ordered dictionary."""
        self._data.move_to_end(key)

    def popitem(self):
        """Remove and return the `(key, value)` pair least recently used."""
        if not self._data:
            raise KeyError('cache is empty')
        key, value = next(iter(self._data.items()))
        del self._data[key]
        self.currsize -= self.getsizeof(value) if self.getsizeof else 1
        return (key, value)