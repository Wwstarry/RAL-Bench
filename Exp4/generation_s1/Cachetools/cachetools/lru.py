from __future__ import annotations

from collections import OrderedDict
from typing import Any, Iterator, Tuple

from .cache import Cache


class LRUCache(Cache):
    """
    Cache with least-recently-used eviction.

    Iteration order is LRU -> MRU.
    Accessing an entry updates its recency.
    """

    __slots__ = ("_LRUCache__order",)

    def __init__(self, maxsize: int, getsizeof=None):
        super().__init__(maxsize=maxsize, getsizeof=getsizeof)
        self.__order: OrderedDict[Any, None] = OrderedDict()

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[Any]:
        # LRU -> MRU, snapshot
        return iter(list(self.__order.keys()))

    def __contains__(self, key: Any) -> bool:
        return key in self._data

    def __getitem__(self, key: Any) -> Any:
        value = self._data[key]
        # update recency
        if key in self.__order:
            self.__order.move_to_end(key, last=True)
        else:
            # should not happen if structures are consistent, but keep robust
            self.__order[key] = None
        return value

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key: Any, value: Any) -> None:
        existed = key in self._data
        super().__setitem__(key, value)
        # If maxsize == 0, super().__setitem__ will evict via popitem().
        # Ensure ordering reflects current state.
        if key in self._data:
            if existed:
                if key in self.__order:
                    self.__order.move_to_end(key, last=True)
                else:
                    self.__order[key] = None
            else:
                self.__order[key] = None
                self.__order.move_to_end(key, last=True)
        else:
            # evicted immediately; remove from order if present
            self.__order.pop(key, None)

        # super may have evicted other keys via our popitem; order maintained there.

    def __delitem__(self, key: Any) -> None:
        super().__delitem__(key)
        self.__order.pop(key, None)

    def pop(self, key: Any, default: Any = Cache.__dict__.get("_Cache__data", object())) -> Any:  # type: ignore
        # Use Cache.pop, but also update order.
        if key in self._data:
            value = super().pop(key)
            self.__order.pop(key, None)
            return value
        # default handling similar to dict:
        if default is not Cache.__dict__.get("_Cache__data", object()):  # unreachable placeholder
            return default
        raise KeyError(key)

    def popitem(self) -> Tuple[Any, Any]:
        # Evict least-recently-used
        if not self._data:
            raise KeyError("cache is empty")
        # Ensure order consistent: drop any stale keys
        while self.__order:
            k, _ = self.__order.popitem(last=False)
            if k in self._data:
                v = self._data.pop(k)
                self.currsize -= self._value_size(v)
                return k, v
        # If order got empty but data not, fallback arbitrary
        k, v = self._data.popitem()
        self.currsize -= self._value_size(v)
        return k, v

    def clear(self) -> None:
        super().clear()
        self.__order.clear()