from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any, Callable, Iterator, Tuple

from .cache import Cache


class TTLCache(Cache):
    """
    LRU cache with per-item time-to-live.

    - Accessing an unexpired item updates its recency.
    - Expired items are treated as missing and are removed lazily.
    """

    __slots__ = ("ttl", "timer", "_TTLCache__order", "_TTLCache__expires")

    def __init__(
        self,
        maxsize: int,
        ttl: float,
        timer: Callable[[], float] = time.monotonic,
        getsizeof=None,
    ):
        super().__init__(maxsize=maxsize, getsizeof=getsizeof)
        self.ttl = float(ttl)
        self.timer = timer
        self.__order: OrderedDict[Any, None] = OrderedDict()  # LRU -> MRU
        self.__expires: dict[Any, float] = {}

    def _is_expired(self, key: Any, now: float | None = None) -> bool:
        if key not in self.__expires:
            return False
        if now is None:
            now = self.timer()
        return now >= self.__expires[key]

    def expire(self, now: float | None = None) -> int:
        if now is None:
            now = self.timer()
        removed = 0
        # Walk order from LRU; expired items are not necessarily clustered, so scan snapshot.
        for k in list(self.__order.keys()):
            if k in self._data and self._is_expired(k, now):
                v = self._data.pop(k)
                self.currsize -= self._value_size(v)
                self.__order.pop(k, None)
                self.__expires.pop(k, None)
                removed += 1
            elif k not in self._data:
                self.__order.pop(k, None)
                self.__expires.pop(k, None)
        # Clean up any data keys missing from order/expiry
        for k in list(self.__expires.keys()):
            if k not in self._data:
                self.__expires.pop(k, None)
        return removed

    def __len__(self) -> int:
        self.expire()
        return len(self._data)

    def __iter__(self) -> Iterator[Any]:
        self.expire()
        return iter(list(self.__order.keys()))

    def __contains__(self, key: Any) -> bool:
        if key not in self._data:
            return False
        if self._is_expired(key):
            # lazily remove
            try:
                self.__delitem__(key)
            except KeyError:
                pass
            return False
        return True

    def __getitem__(self, key: Any) -> Any:
        value = self._data[key]
        if self._is_expired(key):
            # remove and behave like missing
            self.__delitem__(key)
            raise KeyError(key)
        # update recency
        if key in self.__order:
            self.__order.move_to_end(key, last=True)
        else:
            self.__order[key] = None
        return value

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key: Any, value: Any) -> None:
        # purge first so we don't evict unexpired needlessly
        self.expire()
        existed = key in self._data
        super().__setitem__(key, value)
        if key in self._data:
            self.__expires[key] = self.timer() + self.ttl
            if existed:
                if key in self.__order:
                    self.__order.move_to_end(key, last=True)
                else:
                    self.__order[key] = None
            else:
                self.__order[key] = None
                self.__order.move_to_end(key, last=True)
        else:
            # immediately evicted (e.g., maxsize==0)
            self.__order.pop(key, None)
            self.__expires.pop(key, None)

        # Ensure within bounds after setting; base may call our popitem(), which purges
        # expired and maintains structures.

    def __delitem__(self, key: Any) -> None:
        super().__delitem__(key)
        self.__order.pop(key, None)
        self.__expires.pop(key, None)

    def pop(self, key: Any, default: Any = Cache.__dict__.get("_Cache__data", object())) -> Any:  # type: ignore
        # remove expired first for this key
        if key in self._data and self._is_expired(key):
            self.__delitem__(key)
        if key in self._data:
            value = super().pop(key)
            self.__order.pop(key, None)
            self.__expires.pop(key, None)
            return value
        if default is not Cache.__dict__.get("_Cache__data", object()):  # placeholder
            return default
        raise KeyError(key)

    def popitem(self) -> Tuple[Any, Any]:
        # Purge expired first; then evict LRU among unexpired
        self.expire()
        if not self._data:
            raise KeyError("cache is empty")
        while self.__order:
            k, _ = self.__order.popitem(last=False)
            if k in self._data:
                # should be unexpired after expire(), but check anyway
                if self._is_expired(k):
                    v = self._data.pop(k)
                    self.currsize -= self._value_size(v)
                    self.__expires.pop(k, None)
                    continue
                v = self._data.pop(k)
                self.currsize -= self._value_size(v)
                self.__expires.pop(k, None)
                return k, v
            self.__expires.pop(k, None)
        # Fallback: arbitrary
        k, v = self._data.popitem()
        self.currsize -= self._value_size(v)
        self.__expires.pop(k, None)
        return k, v

    def clear(self) -> None:
        super().clear()
        self.__order.clear()
        self.__expires.clear()

    # snapshot-style views with expiry purge
    def keys(self):
        self.expire()
        return list(self.__order.keys())

    def values(self):
        self.expire()
        return [self._data[k] for k in list(self.__order.keys()) if k in self._data]

    def items(self):
        self.expire()
        return [(k, self._data[k]) for k in list(self.__order.keys()) if k in self._data]