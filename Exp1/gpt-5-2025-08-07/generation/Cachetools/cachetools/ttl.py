import time
from collections import OrderedDict
from collections.abc import Iterator
from typing import Callable

from .cache import Cache, _default_getsizeof


class TTLCache(Cache):
    """
    Cache with time-to-live eviction for entries.

    Entries expire automatically according to ttl. Access updates LRU order.
    Expired entries are treated as missing and are purged lazily on access.
    """

    def __init__(self, maxsize: int, ttl: float, timer: Callable | None = None, getsizeof: Callable | None = None):
        super().__init__(maxsize, getsizeof or _default_getsizeof)
        if ttl is None:
            raise TypeError("ttl must be a number, not None")
        self.ttl = float(ttl)
        self.timer = timer or time.monotonic
        # mapping: key -> (value, expire_at, size)
        self._data: OrderedDict = OrderedDict()

    def _now(self) -> float:
        return float(self.timer())

    def _expired(self, expire_at: float) -> bool:
        return expire_at <= self._now()

    def _purge(self):
        # Remove expired entries across the cache.
        if not self._data:
            return
        # Iterate over keys and remove expired ones
        to_delete = []
        now = self._now()
        for k, (v, exp, sz) in self._data.items():
            if exp <= now:
                to_delete.append(k)
        for k in to_delete:
            v, exp, sz = self._data.pop(k)
            self.currsize -= sz

    def __len__(self) -> int:
        self._purge()
        return len(self._data)

    def __contains__(self, key) -> bool:
        # Purge just this key or globally for correctness
        if key in self._data:
            v, exp, sz = self._data[key]
            if self._expired(exp):
                # Remove expired
                self._data.pop(key, None)
                self.currsize -= sz
                return False
            return True
        return False

    def __getitem__(self, key):
        try:
            v, exp, sz = self._data[key]
        except KeyError:
            raise
        if self._expired(exp):
            self._data.pop(key, None)
            self.currsize -= sz
            raise KeyError(key)
        # update-on-access: mark as most recent
        self._data.move_to_end(key)
        return v

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __setitem__(self, key, value):
        # purge expired entries first to free space
        self._purge()
        size = self.getsizeof(value)
        expire_at = self._now() + self.ttl
        if key in self._data:
            old_v, old_exp, old_sz = self._data[key]
            # replace and move to end
            self.currsize -= old_sz
            self._data[key] = (value, expire_at, size)
            self._data.move_to_end(key)
        else:
            self._data[key] = (value, expire_at, size)
        self.currsize += size
        self._trim()

    def setdefault(self, key, default=None):
        # If exists and not expired, return and promote
        if key in self._data:
            try:
                return self.__getitem__(key)
            except KeyError:
                # was expired, treat as missing and fall through to set
                pass
        self.__setitem__(key, default)
        return default

    def popitem(self):
        # Purge expired first; then pop least-recently-used
        self._purge()
        if not self._data:
            raise KeyError("popitem(): cache is empty")
        key, (v, exp, sz) = self._data.popitem(last=False)
        self.currsize -= sz
        return key, v

    def __delitem__(self, key):
        if key in self._data:
            v, exp, sz = self._data.pop(key)
            self.currsize -= sz
        else:
            raise KeyError(key)

    def __iter__(self) -> Iterator:
        # Before iterating, purge expired entries
        self._purge()
        return iter(self._data)

    def clear(self):
        self._data.clear()
        self.currsize = 0
        self._data = OrderedDict()