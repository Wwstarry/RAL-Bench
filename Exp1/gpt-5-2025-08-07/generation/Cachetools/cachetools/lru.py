from collections import OrderedDict
from collections.abc import Iterator
from typing import Callable

from .cache import Cache, _default_getsizeof


class LRUCache(Cache):
    """
    Least-Recently-Used cache, update-on-access semantics.

    Uses an OrderedDict to maintain access order. Accessing or setting a key
    moves it to the end (most recent). Eviction removes least-recently-used.
    """

    def __init__(self, maxsize: int, getsizeof: Callable | None = None):
        super().__init__(maxsize, getsizeof or _default_getsizeof)
        self._data = OrderedDict()

    def __getitem__(self, key):
        try:
            value = self._data[key]
        except KeyError:
            raise
        # update-on-access: mark as most recent
        self._data.move_to_end(key)
        return value

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __setitem__(self, key, value):
        if key in self._data:
            old = self._data[key]
            self.currsize -= self.getsizeof(old)
            # Replace value and move to end
            self._data[key] = value
            self._data.move_to_end(key)
        else:
            self._data[key] = value
        self.currsize += self.getsizeof(value)
        self._trim()

    def setdefault(self, key, default=None):
        if key in self._data:
            # Access existing and move to end
            val = self.__getitem__(key)
            return val
        else:
            self.__setitem__(key, default)
            return default

    def popitem(self):
        if not self._data:
            raise KeyError("popitem(): cache is empty")
        # Pop least-recently-used (first item)
        key, value = self._data.popitem(last=False)
        self.currsize -= self.getsizeof(value)
        return key, value

    def __iter__(self) -> Iterator:
        # Iterate from LRU to MRU
        return iter(self._data)

    def update(self, other=(), /, **kwargs):
        super().update(other, **kwargs)

    def clear(self):
        super().clear()
        # ensure underlying type remains OrderedDict
        self._data = OrderedDict()