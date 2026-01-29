from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, Callable, Dict, Iterable, Iterator, Mapping, Optional, Tuple


_MISSING = object()


class Cache(MutableMapping):
    """
    Base cache implementing dict-like access and bounded size.

    Semantics:
    - maxsize bounds currsize (count if getsizeof is None, else sum(getsizeof(v))).
    - Subclasses implement popitem() eviction policy.
    """

    __slots__ = ("maxsize", "currsize", "getsizeof", "_Cache__data")

    def __init__(self, maxsize: int, getsizeof: Optional[Callable[[Any], int]] = None):
        self.maxsize = maxsize
        self.getsizeof = getsizeof
        self.__data: Dict[Any, Any] = {}
        self.currsize = 0

    # ---- internal helpers ----
    def _value_size(self, value: Any) -> int:
        if self.getsizeof is None:
            return 1
        size = self.getsizeof(value)
        try:
            size = int(size)
        except Exception:
            size = 1
        return size

    def _recompute_currsize(self) -> int:
        if self.getsizeof is None:
            self.currsize = len(self.__data)
        else:
            self.currsize = sum(self._value_size(v) for v in self.__data.values())
        return self.currsize

    def _maybe_evict(self) -> None:
        # Evict until within bounds. maxsize can be 0; then we will evict all.
        while self.currsize > self.maxsize and len(self.__data) > 0:
            self.popitem()

    # ---- MutableMapping interface ----
    def __len__(self) -> int:
        return len(self.__data)

    def __iter__(self) -> Iterator[Any]:
        # Snapshot to avoid surprises on mutation during iteration.
        return iter(list(self.__data.keys()))

    def __contains__(self, key: Any) -> bool:
        return key in self.__data

    def __getitem__(self, key: Any) -> Any:
        return self.__data[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        if key in self.__data:
            old = self.__data[key]
            self.__data[key] = value
            if self.getsizeof is not None:
                self.currsize += self._value_size(value) - self._value_size(old)
            # else currsize unchanged since count unchanged
        else:
            self.__data[key] = value
            self.currsize += self._value_size(value)
        self._maybe_evict()

    def __delitem__(self, key: Any) -> None:
        value = self.__data.pop(key)
        self.currsize -= self._value_size(value)

    # ---- dict-like helpers ----
    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def pop(self, key: Any, default: Any = _MISSING) -> Any:
        if key in self.__data:
            value = self.__data.pop(key)
            self.currsize -= self._value_size(value)
            return value
        if default is _MISSING:
            raise KeyError(key)
        return default

    def popitem(self) -> Tuple[Any, Any]:
        raise NotImplementedError

    def clear(self) -> None:
        self.__data.clear()
        self.currsize = 0

    def setdefault(self, key: Any, default: Any = None) -> Any:
        if key in self.__data:
            return self.__data[key]
        self[key] = default
        # If maxsize == 0, insertion will be immediately evicted; emulate dict.setdefault:
        # return the inserted value even if evicted.
        return default

    def update(self, *args: Any, **kwargs: Any) -> None:
        if args:
            if len(args) > 1:
                raise TypeError(f"update expected at most 1 positional argument, got {len(args)}")
            other = args[0]
            if hasattr(other, "items"):
                for k, v in other.items():
                    self[k] = v
            else:
                for k, v in other:
                    self[k] = v
        for k, v in kwargs.items():
            self[k] = v

    # Provide mapping views as snapshots (sufficient for tests expecting iterables).
    def keys(self) -> Iterable[Any]:
        return list(self.__data.keys())

    def values(self) -> Iterable[Any]:
        return list(self.__data.values())

    def items(self) -> Iterable[Tuple[Any, Any]]:
        return list(self.__data.items())

    # ---- representation ----
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({dict(self.items())}, maxsize={self.maxsize}, currsize={self.currsize})"

    # ---- protected access for subclasses ----
    @property
    def _data(self) -> Dict[Any, Any]:
        return self.__data