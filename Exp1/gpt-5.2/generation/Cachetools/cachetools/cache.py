from __future__ import annotations

import time as _time
from collections import OrderedDict
from threading import RLock
from typing import Any, Dict, Iterable, Iterator, MutableMapping, Optional, Tuple


class Cache(MutableMapping):
    """
    Base cache implementation with a maxsize and eviction via popitem().

    Behaves like a dict for the common operations used by cachetools:
    - __getitem__/__setitem__/__delitem__
    - __contains__ (via MutableMapping)
    - get, pop, setdefault, update, clear
    - popitem (eviction hook, implemented by subclasses)
    """

    __marker = object()

    def __init__(self, maxsize: int, getsizeof=None) -> None:
        if maxsize is None:
            raise TypeError("maxsize must be an int")
        self.maxsize = maxsize
        self.getsizeof = getsizeof or (lambda value: 1)
        self._Cache__data: Dict[Any, Any] = {}
        self._Cache__currsize: int = 0
        self._Cache__lock = RLock()

    @property
    def currsize(self) -> int:
        return self._Cache__currsize

    def __len__(self) -> int:
        return len(self._Cache__data)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._Cache__data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(maxsize={self.maxsize}, currsize={self.currsize})"

    def clear(self) -> None:
        with self._Cache__lock:
            self._Cache__data.clear()
            self._Cache__currsize = 0

    def __getitem__(self, key: Any) -> Any:
        with self._Cache__lock:
            return self._Cache__data[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        with self._Cache__lock:
            size = self.getsizeof(value)
            if size < 0:
                size = 0

            data = self._Cache__data
            if key in data:
                old = data[key]
                self._Cache__currsize -= self.getsizeof(old)
            data[key] = value
            self._Cache__currsize += size

            self._evict()

    def __delitem__(self, key: Any) -> None:
        with self._Cache__lock:
            data = self._Cache__data
            value = data.pop(key)
            self._Cache__currsize -= self.getsizeof(value)

    def _evict(self) -> None:
        if self.maxsize is None:
            return
        # Evict until size constraint satisfied.
        while self.currsize > self.maxsize and len(self._Cache__data):
            self.popitem()

    def pop(self, key: Any, default: Any = __marker) -> Any:
        with self._Cache__lock:
            if default is self.__marker:
                value = self._Cache__data.pop(key)  # may raise KeyError
                self._Cache__currsize -= self.getsizeof(value)
                return value
            value = self._Cache__data.pop(key, self.__marker)
            if value is self.__marker:
                return default
            self._Cache__currsize -= self.getsizeof(value)
            return value

    def setdefault(self, key: Any, default: Any = None) -> Any:
        with self._Cache__lock:
            try:
                return self[key]
            except KeyError:
                self[key] = default
                return default

    def popitem(self) -> Tuple[Any, Any]:
        """
        Remove and return an item (key, value). Subclasses decide which item.
        """
        with self._Cache__lock:
            key, value = self._Cache__data.popitem()
            self._Cache__currsize -= self.getsizeof(value)
            return key, value

    def __getstate__(self):
        return {
            "maxsize": self.maxsize,
            "getsizeof": self.getsizeof,
            "data": dict(self._Cache__data),
            "currsize": self._Cache__currsize,
        }

    def __setstate__(self, state):
        self.maxsize = state["maxsize"]
        self.getsizeof = state["getsizeof"]
        self._Cache__data = dict(state["data"])
        self._Cache__currsize = state.get("currsize", 0)
        self._Cache__lock = RLock()


class LRUCache(Cache):
    """
    Least-Recently-Used cache.
    Accessing a key updates its recency.
    """

    def __init__(self, maxsize: int, getsizeof=None) -> None:
        super().__init__(maxsize, getsizeof=getsizeof)
        # Replace underlying mapping with OrderedDict for LRU ordering.
        self._Cache__data = OrderedDict()

    def __getitem__(self, key: Any) -> Any:
        with self._Cache__lock:
            data: OrderedDict = self._Cache__data  # type: ignore[assignment]
            value = data[key]
            data.move_to_end(key, last=True)
            return value

    def __setitem__(self, key: Any, value: Any) -> None:
        with self._Cache__lock:
            data: OrderedDict = self._Cache__data  # type: ignore[assignment]

            size = self.getsizeof(value)
            if size < 0:
                size = 0

            if key in data:
                old = data[key]
                self._Cache__currsize -= self.getsizeof(old)
                data[key] = value
                data.move_to_end(key, last=True)
            else:
                data[key] = value
                data.move_to_end(key, last=True)
            self._Cache__currsize += size

            self._evict()

    def popitem(self) -> Tuple[Any, Any]:
        with self._Cache__lock:
            data: OrderedDict = self._Cache__data  # type: ignore[assignment]
            key, value = data.popitem(last=False)
            self._Cache__currsize -= self.getsizeof(value)
            return key, value


class TTLCache(LRUCache):
    """
    LRU cache with per-item TTL expiration.

    Expired entries are treated as missing:
    - __getitem__ raises KeyError
    - __contains__ returns False
    - iter/len/items/keys/values behave as if expired items aren't present
    """

    def __init__(self, maxsize: int, ttl: float, timer=_time.monotonic, getsizeof=None) -> None:
        if ttl is None:
            raise TypeError("ttl must be a number")
        super().__init__(maxsize, getsizeof=getsizeof)
        self.ttl = ttl
        self.timer = timer
        self.__expires: Dict[Any, float] = {}

    def _expire(self, now: Optional[float] = None) -> None:
        if now is None:
            now = self.timer()
        # Remove expired keys. Iterate over a snapshot to avoid runtime errors.
        expired = [k for k, exp in list(self.__expires.items()) if exp <= now]
        for k in expired:
            # Use base deletion to maintain size.
            try:
                super(LRUCache, self).__delitem__(k)  # call Cache.__delitem__
            except KeyError:
                pass
            self.__expires.pop(k, None)

    def __len__(self) -> int:
        with self._Cache__lock:
            self._expire()
            return super().__len__()

    def __iter__(self) -> Iterator[Any]:
        with self._Cache__lock:
            self._expire()
            # iterate over a snapshot (stable even if user mutates)
            return iter(list(self._Cache__data.keys()))

    def __contains__(self, key: object) -> bool:
        with self._Cache__lock:
            self._expire()
            return key in self._Cache__data

    def __getitem__(self, key: Any) -> Any:
        with self._Cache__lock:
            now = self.timer()
            exp = self.__expires.get(key)
            if exp is None or exp <= now:
                if exp is not None:
                    # remove stale
                    self._expire(now)
                raise KeyError(key)
            # LRU update on access
            return super().__getitem__(key)

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key: Any, value: Any) -> None:
        with self._Cache__lock:
            now = self.timer()
            self._expire(now)
            super().__setitem__(key, value)
            self.__expires[key] = now + self.ttl

    def __delitem__(self, key: Any) -> None:
        with self._Cache__lock:
            self._expire()
            super(LRUCache, self).__delitem__(key)  # Cache.__delitem__
            self.__expires.pop(key, None)

    def pop(self, key: Any, default: Any = Cache._Cache__marker) -> Any:  # type: ignore[attr-defined]
        with self._Cache__lock:
            self._expire()
            if default is Cache._Cache__marker:  # type: ignore[attr-defined]
                value = super(LRUCache, self).pop(key)  # Cache.pop
            else:
                value = super(LRUCache, self).pop(key, default)  # Cache.pop
            self.__expires.pop(key, None)
            return value

    def popitem(self) -> Tuple[Any, Any]:
        with self._Cache__lock:
            self._expire()
            key, value = super().popitem()
            self.__expires.pop(key, None)
            return key, value

    def clear(self) -> None:
        with self._Cache__lock:
            super().clear()
            self.__expires.clear()

    def __getstate__(self):
        state = super().__getstate__()
        state.update(
            {
                "ttl": self.ttl,
                "timer": self.timer,
                "expires": dict(self.__expires),
            }
        )
        return state

    def __setstate__(self, state):
        super().__setstate__(state)
        self.ttl = state["ttl"]
        self.timer = state["timer"]
        self.__expires = dict(state.get("expires", {}))