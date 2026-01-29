from collections import OrderedDict
from .cache import Cache

class LRUCache(Cache):
    """LRU (least recently used) cache implementation."""

    def __init__(self, maxsize, missing=None, getsizeof=None):
        super().__init__(maxsize, missing, getsizeof)
        self._Cache__data = OrderedDict()

    def __getitem__(self, key):
        try:
            value = self._Cache__data.pop(key)
            self._Cache__data[key] = value  # move to end (most recently used)
            return value
        except KeyError:
            if self.missing is not None:
                return self.missing(self, key)
            raise

    def __setitem__(self, key, value):
        data = self._Cache__data
        if key in data:
            data.pop(key)
        data[key] = value
        while self.maxsize is not None and len(data) > self.maxsize:
            data.popitem(last=False)

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
        return self._Cache__data.popitem(last=False)