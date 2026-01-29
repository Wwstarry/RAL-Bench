import collections
from collections.abc import MutableMapping
from typing import Callable, Iterator


def _default_getsizeof(value) -> int:
    return 1


class Cache(MutableMapping):
    """
    Basic cache implementation with a size limit and optional item sizing.

    This base class provides dictionary-like semantics and tracks a weighted
    current size, evicting items by popitem() until currsize <= maxsize.

    Subclasses should override popitem() to implement specific eviction policy.
    """

    def __init__(self, maxsize: int, getsizeof: Callable | None = None):
        if maxsize is None:
            raise TypeError("maxsize must be an integer, not None")
        self.maxsize = int(maxsize)
        self.getsizeof = getsizeof or _default_getsizeof
        self._data: dict = {}
        self.currsize: int = 0

    # Core mapping protocol

    def __getitem__(self, key):
        # No special access policy in base cache
        value = self._data[key]
        return value

    def __setitem__(self, key, value):
        # Adjust size
        if key in self._data:
            old = self._data[key]
            self.currsize -= self.getsizeof(old)
        self._data[key] = value
        self.currsize += self.getsizeof(value)
        self._trim()

    def __delitem__(self, key):
        if key in self._data:
            val = self._data.pop(key)
            self.currsize -= self.getsizeof(val)
        else:
            raise KeyError(key)

    def __iter__(self) -> Iterator:
        # Iteration order is insertion order for base cache
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def clear(self) -> None:
        self._data.clear()
        self.currsize = 0

    def popitem(self):
        """
        Pop and return an arbitrary item (key, value).

        Subclasses override this to implement eviction policy (e.g., LRU).
        """
        try:
            key, value = self._data.popitem()
        except KeyError:
            raise KeyError("popitem(): cache is empty")
        self.currsize -= self.getsizeof(value)
        return key, value

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def setdefault(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            self.__setitem__(key, default)
            return default

    def update(self, other=(), /, **kwargs):
        if isinstance(other, MutableMapping):
            iterable = other.items()
        else:
            iterable = other
        for k, v in iterable:
            self[k] = v
        for k, v in kwargs.items():
            self[k] = v

    def __contains__(self, key) -> bool:
        return key in self._data

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(maxsize={self.maxsize!r}, currsize={self.currsize!r})"

    # Internal helpers

    def _trim(self):
        # Evict until within capacity
        if self.maxsize < 0:
            # negative maxsize treated as zero
            self.maxsize = 0
        while self.currsize > self.maxsize and self._data:
            self.popitem()