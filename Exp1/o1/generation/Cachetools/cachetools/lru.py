from collections import OrderedDict
from .cache import Cache

class LRUCache(Cache):
    """
    Least Recently Used (LRU) cache implementation. Discards the
    least recently used items first when maxsize is reached.
    Accessing (retrieving or setting) an item updates its position.
    """

    def __init__(self, maxsize=128):
        super().__init__(maxsize)
        self._store = OrderedDict()

    def __getitem__(self, key):
        value = self._store[key]
        self._store.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        self._check_size()

    def _check_size(self):
        if self.maxsize is not None:
            while len(self._store) > self.maxsize:
                self._store.popitem(last=False)