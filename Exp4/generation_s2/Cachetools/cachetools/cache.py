from __future__ import annotations

from collections.abc import Iterable, Iterator, MutableMapping
from typing import Any, Callable, Optional


class Cache(MutableMapping):
    """
    Base cache implementing the dictionary-like API with a maxsize constraint.

    Subclasses may override:
      - __getitem__/__setitem__/__delitem__ for policy hooks
      - popitem for eviction policy
      - __iter__/__len__ if storage differs
    """

    __slots__ = ("maxsize", "currsize", "_Cache__data", "getsizeof")

    def __init__(self, maxsize: int, getsizeof: Optional[Callable[[Any], int]] = None):
        if maxsize is None:
            raise TypeError("maxsize must not be None")
        self.maxsize = maxsize
        self.getsizeof = getsizeof or (lambda value: 1)
        self.currsize = 0
        self.__data: dict[Any, Any] = {}

    # -- internal helpers -------------------------------------------------

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({dict(self)!r}, maxsize={self.maxsize!r}, currsize={self.currsize!r})"

    def __len__(self) -> int:
        return len(self.__data)

    def __iter__(self) -> Iterator:
        return iter(self.__data)

    def __contains__(self, key: object) -> bool:
        return key in self.__data

    def __getitem__(self, key: Any) -> Any:
        return self.__data[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        size = self.getsizeof(value)
        if size < 0:
            raise ValueError("value size must be >= 0")
        if key in self.__data:
            # update: adjust size delta
            old = self.__data[key]
            self.currsize -= self.getsizeof(old)
        self.__data[key] = value
        self.currsize += size
        self._trim()

    def __delitem__(self, key: Any) -> None:
        value = self.__data.pop(key)
        self.currsize -= self.getsizeof(value)

    def clear(self) -> None:
        self.__data.clear()
        self.currsize = 0

    def copy(self):
        return dict(self)

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def pop(self, key: Any, default: Any = None) -> Any:
        if default is None:
            value = self.__data.pop(key)  # may raise KeyError
            self.currsize -= self.getsizeof(value)
            return value
        try:
            value = self.__data.pop(key)
        except KeyError:
            return default
        else:
            self.currsize -= self.getsizeof(value)
            return value

    def popitem(self):
        # Base behavior matches dict.popitem (LIFO in CPython >= 3.7)
        key, value = self.__data.popitem()
        self.currsize -= self.getsizeof(value)
        return key, value

    def setdefault(self, key: Any, default: Any = None) -> Any:
        if key in self:
            return self[key]
        self[key] = default
        return default

    def update(self, *args, **kwargs) -> None:
        if args:
            if len(args) > 1:
                raise TypeError(f"update expected at most 1 arguments, got {len(args)}")
            other = args[0]
            if isinstance(other, MutableMapping):
                for k, v in other.items():
                    self[k] = v
            elif isinstance(other, Iterable):
                for k, v in other:
                    self[k] = v
            else:
                raise TypeError("update() argument must be a mapping or iterable of pairs")
        for k, v in kwargs.items():
            self[k] = v

    # -- eviction ---------------------------------------------------------

    def _trim(self) -> None:
        """Evict until within maxsize."""
        if self.maxsize is None:
            return
        # maxsize is an int; treat <= 0 as always-empty cache
        while self.currsize > self.maxsize and len(self.__data) > 0:
            self.popitem()