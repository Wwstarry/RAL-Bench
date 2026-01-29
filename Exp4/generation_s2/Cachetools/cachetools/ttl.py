from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any, Callable, Optional

from .cache import Cache


class TTLCache(Cache):
    """
    Cache with per-item time-to-live expiration.

    Items are treated as missing once expired.
    Eviction policy among live items is LRU.
    """

    __slots__ = ("ttl", "_TTLCache__order", "_TTLCache__expires", "_TTLCache__timer")

    def __init__(
        self,
        maxsize: int,
        ttl: float,
        timer: Optional[Callable[[], float]] = None,
        getsizeof: Optional[Callable[[Any], int]] = None,
    ):
        super().__init__(maxsize, getsizeof=getsizeof)
        self.ttl = float(ttl)
        self.__timer = timer or time.monotonic
        self.__order: OrderedDict[Any, None] = OrderedDict()
        self.__expires: dict[Any, float] = {}

    def _now(self) -> float:
        return float(self.__timer())

    def _expire(self, now: Optional[float] = None) -> None:
        if now is None:
            now = self._now()
        if not self.__expires:
            return
        dead = [k for k, exp in list(self.__expires.items()) if exp <= now]
        for k in dead:
            if k in self:
                try:
                    super().__delitem__(k)
                except KeyError:
                    pass
            self.__expires.pop(k, None)
            self.__order.pop(k, None)

    def __contains__(self, key: object) -> bool:
        exp = self.__expires.get(key)  # type: ignore[arg-type]
        if exp is None:
            return False
        if exp <= self._now():
            try:
                self.__delitem__(key)  # type: ignore[arg-type]
            except KeyError:
                self.__expires.pop(key, None)  # type: ignore[arg-type]
                self.__order.pop(key, None)  # type: ignore[arg-type]
            return False
        return super().__contains__(key)

    def __getitem__(self, key: Any) -> Any:
        exp = self.__expires.get(key)
        if exp is None:
            raise KeyError(key)
        if exp <= self._now():
            self.__delitem__(key)
            raise KeyError(key)
        value = super().__getitem__(key)
        if key in self.__order:
            self.__order.move_to_end(key, last=True)
        else:
            self.__order[key] = None
        return value

    def __setitem__(self, key: Any, value: Any) -> None:
        now = self._now()
        self._expire(now)
        existed = key in self
        super().__setitem__(key, value)
        self.__expires[key] = now + self.ttl
        if existed and key in self.__order:
            self.__order.move_to_end(key, last=True)
        else:
            self.__order[key] = None

    def __delitem__(self, key: Any) -> None:
        super().__delitem__(key)
        self.__expires.pop(key, None)
        self.__order.pop(key, None)

    def popitem(self):
        self._expire()
        if not self.__order:
            raise KeyError("popitem(): cache is empty")
        key, _ = self.__order.popitem(last=False)
        value = super().__getitem__(key)
        super().__delitem__(key)
        self.__expires.pop(key, None)
        return key, value

    def __len__(self) -> int:
        self._expire()
        return super().__len__()

    def __iter__(self):
        self._expire()
        return super().__iter__()

    def clear(self) -> None:
        super().clear()
        self.__expires.clear()
        self.__order.clear()