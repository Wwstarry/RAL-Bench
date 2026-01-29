import collections.abc

class Cache(collections.abc.MutableMapping):
    """Base cache class implementing a dict-like interface."""

    def __init__(self, maxsize=None, missing=None):
        if maxsize is not None:
            if not isinstance(maxsize, int) or maxsize < 0:
                raise ValueError("maxsize should be a non-negative integer or None")
        self.maxsize = maxsize
        self._Cache__data = dict()
        self._Cache__missing = missing

    def __getitem__(self, key):
        try:
            return self._Cache__data[key]
        except KeyError:
            if self._Cache__missing is not None:
                value = self._Cache__missing(key)
                self[key] = value
                return value
            raise

    def __setitem__(self, key, value):
        self._Cache__data[key] = value
        self._evict()

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

    def pop(self, key, default=None):
        return self._Cache__data.pop(key, default)

    def popitem(self):
        return self._Cache__data.popitem()

    def get(self, key, default=None):
        return self._Cache__data.get(key, default)

    def setdefault(self, key, default=None):
        if key not in self._Cache__data:
            self[key] = default
        return self._Cache__data[key]

    def _evict(self):
        """Evict items if needed. Base class does nothing."""
        pass