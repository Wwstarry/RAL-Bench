class Cache:
    """
    Base cache class that resembles a dictionary and can serve
    as a parent class for more specialized cache implementations.
    """

    def __init__(self, maxsize=None):
        """
        Initialize the cache with an optional maximum size. If maxsize
        is None, the cache has no upper size limit.
        """
        self.maxsize = maxsize
        self._store = {}

    def __contains__(self, key):
        return key in self._store

    def __getitem__(self, key):
        return self._store[key]

    def __setitem__(self, key, value):
        self._store[key] = value

    def __delitem__(self, key):
        del self._store[key]

    def __len__(self):
        return len(self._store)

    def __iter__(self):
        return iter(self._store)

    def clear(self):
        """Clear the cache."""
        self._store.clear()

    def get(self, key, default=None):
        """Return the value for key if key is in the cache, else default."""
        return self._store.get(key, default)

    def pop(self, key, *args):
        """
        Remove specified key and return the corresponding value.
        If key is not found, default is returned if given, otherwise
        KeyError is raised.
        """
        if len(args) > 1:
            raise TypeError("pop expected at most 2 arguments, got {}".format(1 + len(args)))
        try:
            return self._store.pop(key)
        except KeyError:
            if args:
                return args[0]
            raise

    def popitem(self):
        """
        Remove and return an arbitrary (key, value) pair from the cache.
        Raises KeyError if the cache is empty.
        """
        return self._store.popitem()

    def setdefault(self, key, default=None):
        """If key is in the cache, return its value. If not, insert key with default."""
        return self._store.setdefault(key, default)

    def update(self, *args, **kwargs):
        """Update the cache with the key/value pairs from other, overwriting existing keys."""
        self._store.update(*args, **kwargs)

    def keys(self):
        return self._store.keys()

    def items(self):
        return self._store.items()

    def values(self):
        return self._store.values()

    def __repr__(self):
        return "{}(maxsize={}, size={})".format(
            self.__class__.__name__, self.maxsize, len(self._store)
        )