import collections.abc

class Cache(collections.abc.MutableMapping):
    """Mutable mapping to serve as a base class for cache implementations."""

    def __init__(self, maxsize, getsizeof=None):
        if getsizeof is None:
            self.__getsizeof = lambda x: 1
        else:
            self.__getsizeof = getsizeof
        self.__maxsize = maxsize
        self.__currsize = 0
        self.__data = {}

    def __repr__(self):
        return '%s(%r, maxsize=%r, currsize=%r)' % (
            self.__class__.__name__,
            list(self.__data.items()),
            self.__maxsize,
            self.__currsize,
        )

    def __getitem__(self, key):
        try:
            return self.__data[key]
        except KeyError:
            return self.__missing__(key)

    def __setitem__(self, key, value):
        maxsize = self.__maxsize
        size = self.getsizeof(value)
        if size > maxsize:
            raise ValueError('value too large')
        
        if key not in self.__data or self.__data[key] is not value:
            existing_size = self.getsizeof(self.__data[key]) if key in self.__data else 0
            while self.__currsize + size - existing_size > maxsize:
                self.popitem()
        
        if key in self.__data:
            diff = size - self.getsizeof(self.__data[key])
            self.__data[key] = value
            self.__currsize += diff
        else:
            self.__data[key] = value
            self.__currsize += size

    def __delitem__(self, key):
        size = self.getsizeof(self.__data[key])
        del self.__data[key]
        self.__currsize -= size

    def __contains__(self, key):
        return key in self.__data

    def __missing__(self, key):
        raise KeyError(key)

    def __iter__(self):
        return iter(self.__data)

    def __len__(self):
        return len(self.__data)

    @property
    def maxsize(self):
        """The maximum size of the cache."""
        return self.__maxsize

    @property
    def currsize(self):
        """The current size of the cache."""
        return self.__currsize

    def getsizeof(self, value):
        """Return the size of a cache element's value."""
        return self.__getsizeof(value)