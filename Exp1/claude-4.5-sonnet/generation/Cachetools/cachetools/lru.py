"""LRU (Least Recently Used) cache implementation."""

import collections


class LRUCache(collections.OrderedDict):
    """Least Recently Used (LRU) cache implementation."""

    def __init__(self, maxsize, getsizeof=None):
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")
        super().__init__()
        self.__maxsize = maxsize
        self.__getsizeof = getsizeof or (lambda x: 1)
        self.__currsize = 0

    def __repr__(self):
        return f"{self.__class__.__name__}({dict(self)!r}, maxsize={self.__maxsize!r}, currsize={self.__currsize!r})"

    def __getitem__(self, key):
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        maxsize = self.__maxsize
        size = self.getsizeof(value)
        if size > maxsize:
            raise ValueError("value too large")
        
        if key in self:
            # Update existing key
            old_size = self.getsizeof(super().__getitem__(key))
            self.__currsize -= old_size
            super().__setitem__(key, value)
            self.__currsize += size
            self.move_to_end(key)
        else:
            # New key - evict if necessary
            while self.__currsize + size > maxsize:
                self.popitem(last=False)
            super().__setitem__(key, value)
            self.__currsize += size

    def __delitem__(self, key):
        value = super().__getitem__(key)
        self.__currsize -= self.getsizeof(value)
        super().__delitem__(key)

    def pop(self, key, *default):
        try:
            value = super().__getitem__(key)
            self.__currsize -= self.getsizeof(value)
            super().__delitem__(key)
            return value
        except KeyError:
            if default:
                return default[0]
            raise

    def popitem(self, last=True):
        """Remove and return a (key, value) pair from the cache.
        
        If last is True (default), LIFO order is used.
        If last is False, FIFO order is used (for LRU eviction).
        """
        key, value = super().popitem(last=last)
        self.__currsize -= self.getsizeof(value)
        return key, value

    def setdefault(self, key, default=None):
        if key in self:
            return self[key]
        else:
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