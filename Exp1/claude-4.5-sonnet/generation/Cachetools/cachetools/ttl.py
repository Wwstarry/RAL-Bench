"""TTL (Time To Live) cache implementation."""

import collections
import time


class TTLCache(collections.OrderedDict):
    """Time-To-Live (TTL) cache implementation."""

    def __init__(self, maxsize, ttl, timer=time.monotonic, getsizeof=None):
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")
        if ttl <= 0:
            raise ValueError("ttl must be positive")
        super().__init__()
        self.__maxsize = maxsize
        self.__ttl = ttl
        self.__timer = timer
        self.__getsizeof = getsizeof or (lambda x: 1)
        self.__currsize = 0
        self.__times = {}

    def __repr__(self):
        return f"{self.__class__.__name__}({dict(self)!r}, maxsize={self.__maxsize!r}, currsize={self.__currsize!r})"

    def __contains__(self, key):
        if not super().__contains__(key):
            return False
        # Check if expired
        if self.__timer() - self.__times[key] > self.__ttl:
            self.__delitem_internal(key)
            return False
        return True

    def __getitem__(self, key):
        self.expire()
        if key not in self:
            raise KeyError(key)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        self.expire()
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
            self.__times[key] = self.__timer()
        else:
            # New key - evict if necessary
            while self.__currsize + size > maxsize:
                self.popitem(last=False)
            super().__setitem__(key, value)
            self.__currsize += size
            self.__times[key] = self.__timer()

    def __delitem__(self, key):
        self.expire()
        self.__delitem_internal(key)

    def __delitem_internal(self, key):
        """Internal delete without expiration check."""
        value = super().__getitem__(key)
        self.__currsize -= self.getsizeof(value)
        super().__delitem__(key)
        del self.__times[key]

    def __iter__(self):
        self.expire()
        return super().__iter__()

    def __len__(self):
        self.expire()
        return super().__len__()

    def get(self, key, default=None):
        self.expire()
        if key in self:
            return super().__getitem__(key)
        return default

    def pop(self, key, *default):
        self.expire()
        try:
            value = super().__getitem__(key)
            self.__currsize -= self.getsizeof(value)
            super().__delitem__(key)
            del self.__times[key]
            return value
        except KeyError:
            if default:
                return default[0]
            raise

    def popitem(self, last=True):
        """Remove and return a (key, value) pair from the cache.
        
        If last is True (default), LIFO order is used.
        If last is False, FIFO order is used (for eviction).
        """
        self.expire()
        key, value = super().popitem(last=last)
        self.__currsize -= self.getsizeof(value)
        del self.__times[key]
        return key, value

    def setdefault(self, key, default=None):
        self.expire()
        if key in self:
            return super().__getitem__(key)
        else:
            self[key] = default
            return default

    def expire(self, time=None):
        """Remove expired items from the cache."""
        if time is None:
            time = self.__timer()
        keys_to_delete = []
        for key, timestamp in list(self.__times.items()):
            if time - timestamp > self.__ttl:
                keys_to_delete.append(key)
        for key in keys_to_delete:
            self.__delitem_internal(key)

    @property
    def maxsize(self):
        """The maximum size of the cache."""
        return self.__maxsize

    @property
    def currsize(self):
        """The current size of the cache."""
        self.expire()
        return self.__currsize

    @property
    def ttl(self):
        """The time-to-live of cache entries."""
        return self.__ttl

    @property
    def timer(self):
        """The timer function used by the cache."""
        return self.__timer

    def getsizeof(self, value):
        """Return the size of a cache value."""
        return self.__getsizeof(value)