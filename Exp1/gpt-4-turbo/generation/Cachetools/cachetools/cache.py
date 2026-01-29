import collections.abc

class Cache(collections.abc.MutableMapping):
    """Base class for cache implementations."""

    def __init__(self, maxsize, missing=None, getsizeof=None):
        if maxsize is not None and maxsize < 0:
            raise ValueError("maxsize must be >= 0")
        self.maxsize = maxsize
        self._Cache__data = {}
        self.missing = missing
        self.getsizeof = getsizeof or (lambda x: 1)

    def __getitem__(self, key):
        try:
            return self._Cache__data[key]
        except KeyError:
            if self.missing is not None:
                return self.missing(self, key)
            raise

    def __setitem__(self, key, value):
        self._Cache__data[key] = value

    def __delitem__(self, key):
        del self._Cache__data[key]

    def __contains__(self, key):
        return key in self._Cache__data

    def __len__(self):
        return len(self._Cache__data)

    def __iter__(self):
        return iter(self._Cache__data)

    def clear(self):
        self._Cache__data.clear()

    def popitem(self):
        return self._Cache__data.popitem()

    def __repr__(self):
        return (
            f"{type(self).__name__}({self.maxsize}, {self._Cache__data})"
        )