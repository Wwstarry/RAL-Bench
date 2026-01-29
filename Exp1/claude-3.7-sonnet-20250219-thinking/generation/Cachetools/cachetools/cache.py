"""Memoizing mapping implementations."""

import collections
import functools


class Cache(collections.MutableMapping):
    """Mutable mapping to serve as a simple cache or cache base class."""

    def __init__(self, maxsize, getsizeof=None):
        if maxsize is not None and maxsize < 0:
            raise ValueError('maxsize must be non-negative')
        self.maxsize = maxsize
        self.getsizeof = getsizeof
        self.currsize = 0
        self._data = {}

    def __getitem__(self, key):
        try:
            value = self._data[key]
        except KeyError:
            raise
        self.__on_access__(key)
        return value

    def __setitem__(self, key, value):
        size = self.getsizeof(value) if self.getsizeof else 1
        if self.maxsize is not None:
            if size > self.maxsize:
                raise ValueError('value too large')
            if key not in self._data:
                while self.currsize + size > self.maxsize and self:
                    self.popitem()
        if key in self._data:
            self.__delitem__(key)
        self._data[key] = value
        self.currsize += size

    def __delitem__(self, key):
        value = self._data[key]
        size = self.getsizeof(value) if self.getsizeof else 1
        del self._data[key]
        self.currsize -= size

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __on_access__(self, key):
        """Called when a key is accessed."""
        pass

    def popitem(self):
        """Remove and return the `(key, value)` pair least recently used."""
        try:
            key = next(iter(self._data))
        except StopIteration:
            raise KeyError('cache is empty')
        value = self._data[key]
        del self._data[key]
        return (key, value)

    def clear(self):
        """Clear the cache."""
        self._data.clear()
        self.currsize = 0