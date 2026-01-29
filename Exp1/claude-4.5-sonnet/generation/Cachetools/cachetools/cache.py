"""Base cache implementation."""

import collections.abc


class Cache(collections.abc.MutableMapping):
    """Base cache class."""

    def __init__(self, maxsize, getsizeof=None):
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")
        self.__data = {}
        self.__maxsize = maxsize
        self.__currsize = 0
        self.__getsizeof = getsizeof or (lambda x: 1)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__data!r}, maxsize={self.__maxsize!r}, currsize={self.__currsize!r})"

    def __getitem__(self, key):
        return self.__data[key]

    def __setitem__(self, key, value):
        maxsize = self.__maxsize
        size = self.getsizeof(value)
        if size > maxsize:
            raise ValueError("value too large")
        if key not in self.__data or self.getsizeof(self.__data[key]) < size:
            while self.__currsize + size > maxsize:
                self.popitem()
        if key in self.__data:
            self.__currsize -= self.getsizeof(self.__data[key])
        self.__data[key] = value
        self.__currsize += size

    def __delitem__(self, key):
        value = self.__data.pop(key)
        self.__currsize -= self.getsizeof(value)

    def __contains__(self, key):
        return key in self.__data

    def __missing__(self, key):
        raise KeyError(key)

    def __iter__(self):
        return iter(self.__data)

    def __len__(self):
        return len(self.__data)

    def get(self, key, default=None):
        if key in self:
            return self[key]
        else:
            return default

    def pop(self, key, *default):
        try:
            value = self.__data.pop(key)
            self.__currsize -= self.getsizeof(value)
            return value
        except KeyError:
            if default:
                return default[0]
            raise

    def setdefault(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default

    @property
    def maxsize(self):
        """The maximum size of the cache."""
        return self.__maxsize

    @property
    def currsize(self):
        """The current size of the cache."""
        return self.__currsize

    def getsizeof(self, value):
        """Return the size of a cache value."""
        return self.__getsizeof(value)