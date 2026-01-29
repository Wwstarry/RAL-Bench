"""Base classes for caching"""

import collections
import time
from collections import OrderedDict


class Cache(collections.MutableMapping):
    """Base class for caches."""

    def __init__(self, maxsize, getsizeof=None):
        if maxsize is not None and not isinstance(maxsize, int):
            raise TypeError('maxsize must be an integer or None')
        if maxsize is not None and maxsize < 0:
            raise ValueError('maxsize must be a non-negative integer or None')

        self._maxsize = maxsize
        self.__getsizeof = getsizeof if getsizeof is not None else lambda x: 1
        self._data = {}
        self._size = 0

    def __repr__(self):
        return '%s(%s, maxsize=%r, currsize=%r)' % (
            self.__class__.__name__,
            repr(self._data),
            self.maxsize,
            self.currsize
        )

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        size = self.getsizeof(value)
        if self.maxsize is not None and size > self.maxsize:
            raise ValueError('value too large')

        if key in self._data:
            old_size = self.getsizeof(self._data[key])
            self._size -= old_size
        
        while self.maxsize is not None and self.currsize + size > self.maxsize:
            try:
                self.popitem()
            except KeyError:
                break  # cache is empty

        self._data[key] = value
        self._size += size

    def __delitem__(self, key):
        size = self.getsizeof(self._data[key])
        del self._data[key]
        self._size -= size

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    @property
    def maxsize(self):
        """The maximum size of the cache."""
        return self._maxsize

    @property
    def currsize(self):
        """The current size of the cache."""
        return self._size

    @property
    def getsizeof(self):
        """The function used to measure the size of a value."""
        return self.__getsizeof

    def popitem(self):
        """Remove and return an arbitrary (key, value) pair."""
        try:
            key = next(iter(self._data))
        except StopIteration:
            raise KeyError('%s is empty' % self.__class__.__name__) from None
        value = self[key]
        del self[key]
        return (key, value)


class LRUCache(Cache):
    """Least Recently Used (LRU) cache implementation."""

    def __init__(self, maxsize, getsizeof=None):
        super().__init__(maxsize, getsizeof)
        self._data = OrderedDict()

    def __getitem__(self, key):
        value = super().__getitem__(key)
        self._data.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        if key in self._data:
            self._data.move_to_end(key)
        super().__setitem__(key, value)

    def popitem(self):
        """Remove and return the least recently used item."""
        try:
            key, value = self._data.popitem(last=False)
        except KeyError:
            raise KeyError('%s is empty' % self.__class__.__name__) from None
        size = self.getsizeof(value)
        self._size -= size
        return key, value


class TTLCache(Cache):
    """Time To Live (TTL) cache implementation."""

    def __init__(self, maxsize, ttl, timer=time.time, getsizeof=None):
        super().__init__(maxsize, getsizeof)
        self.__ttl = ttl
        self.__timer = timer
        self.__expires = {}

    @property
    def ttl(self):
        """The time-to-live value of the cache."""
        return self.__ttl

    def __getitem__(self, key):
        # This will raise KeyError if the key is not in self._data
        expires = self.__expires[key]
        if self.__timer() > expires:
            # The __delitem__ call is important to remove the expired item
            # from both _data and _expires, and update the size.
            self.__delitem__(key)
            raise KeyError(key)
        return self._data[key]

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.__expires[key] = self.__timer() + self.__ttl

    def __delitem__(self, key):
        super().__delitem__(key)
        del self.__expires[key]

    def __iter__(self):
        self.expire()
        return super().__iter__()

    def __len__(self):
        self.expire()
        return super().__len__()

    def popitem(self):
        """Remove and return an arbitrary item."""
        self.expire()
        key, value = super().popitem()
        del self.__expires[key]
        return key, value

    def expire(self, now=None):
        """Remove expired items from the cache."""
        if now is None:
            now = self.__timer()
        
        expired_keys = [
            key for key, expires_at in self.__expires.items() if expires_at <= now
        ]
        for key in expired_keys:
            try:
                self.__delitem__(key)
            except KeyError:
                # Item might have been removed by other means
                pass