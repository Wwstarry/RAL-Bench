import collections
import time
from collections import OrderedDict


class Cache(OrderedDict):
    """Base class for caches."""

    def __init__(self, maxsize, getsizeof=None):
        if not isinstance(maxsize, int):
            raise TypeError('maxsize must be an integer')
        if maxsize < 0:
            raise ValueError('maxsize must be a non-negative integer')
        super().__init__()
        self._maxsize = maxsize
        self.getsizeof = getsizeof

    @property
    def maxsize(self):
        """The maximum size of the cache."""
        return self._maxsize

    @property
    def currsize(self):
        """The current size of the cache."""
        return len(self)

    def __missing__(self, key):
        """Called by __getitem__ when a key is not in the cache."""
        raise KeyError(key)

    def __repr__(self):
        return '%s(%s, maxsize=%r, currsize=%r)' % (
            self.__class__.__name__,
            super().__repr__(),
            self.maxsize,
            self.currsize,
        )


class LRUCache(Cache):
    """Least Recently Used (LRU) cache implementation."""

    def __getitem__(self, key):
        try:
            value = super().__getitem__(key)
            self.move_to_end(key)
            return value
        except KeyError:
            return self.__missing__(key)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if self.maxsize > 0 and len(self) > self.maxsize:
            self.popitem(last=False)


class TTLCache(Cache):
    """Time To Live (TTL) cache implementation."""

    class _Link:
        __slots__ = ('key', 'expires', 'next', 'prev')

        def __init__(self, key=None, expires=None):
            self.key = key
            self.expires = expires

        def __repr__(self):
            return '%s(%r, %r)' % (self.__class__.__name__, self.key, self.expires)

    def __init__(self, maxsize, ttl, timer=time.monotonic, getsizeof=None):
        super().__init__(maxsize, getsizeof)
        if not callable(timer):
            raise TypeError('timer must be a callable')
        self.__ttl = ttl
        self.__timer = timer
        self.__root = self._Link()
        self.__root.next = self.__root.prev = self.__root
        self.__links = {}

    @property
    def ttl(self):
        """The time-to-live value of the cache."""
        return self.__ttl

    def __contains__(self, key):
        if key not in self.__links:
            return False
        link = self.__links[key]
        return self.__timer() < link.expires

    def __getitem__(self, key):
        try:
            link = self.__links[key]
            if self.__timer() >= link.expires:
                # __delitem__ will be called, and it will raise KeyError
                self.__delitem__(key)
            return super().__getitem__(key)
        except KeyError:
            return self.__missing__(key)

    def __setitem__(self, key, value):
        self.expire()
        expires = self.__timer() + self.__ttl
        super().__setitem__(key, value)

        if key in self.__links:
            link = self.__links[key]
            link.expires = expires
            link.prev.next = link.next
            link.next.prev = link.prev
        else:
            link = self._Link(key, expires)
            self.__links[key] = link

        last = self.__root.prev
        last.next = self.__root.prev = link
        link.prev = last
        link.next = self.__root

        if self.maxsize > 0 and len(self) > self.maxsize:
            self.popitem()

    def __delitem__(self, key):
        super().__delitem__(key)
        link = self.__links.pop(key)
        link.prev.next = link.next
        link.next.prev = link.prev

    def expire(self, time=None):
        """Remove expired items from the cache."""
        if time is None:
            time = self.__timer()
        root = self.__root
        curr = root.next
        while curr is not root and curr.expires < time:
            try:
                self.__delitem__(curr.key)
            except KeyError:
                # Item might have been deleted manually
                curr = curr.next
            else:
                curr = root.next

    def __iter__(self):
        self.expire()
        return super().__iter__()

    def __len__(self):
        self.expire()
        return super().__len__()

    def popitem(self):
        """Remove and return the least recently inserted item."""
        self.expire()
        if not self:
            raise KeyError('%s is empty' % self.__class__.__name__)
        key = next(iter(self))
        value = self.pop(key)
        return (key, value)