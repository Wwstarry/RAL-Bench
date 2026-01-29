from __future__ import annotations

from collections import OrderedDict
from typing import Any, Callable, Optional

from .cache import Cache


class LRUCache(Cache):
    """
    Least-Recently-Used cache.

    Accessing an item marks it as recently used. Insertion and updates also
    mark as recently used. Eviction removes the least recently used item.
    """

    __slots__ = ("_LRUCache__order",)

    def __init__(self, maxsize: int, getsizeof: Optional[Callable[[Any], int]] = None):
        super().__init__(maxsize, getsizeof=getsizeof)
        self.__order: OrderedDict[Any, None] = OrderedDict()

    def __getitem__(self, key: Any) -> Any:
        value = super().__getitem__(key)
        try:
            self.__order.move_to_end(key, last=True)
        except KeyError:
            self.__order[key] = None
        return value

    def __setitem__(self, key: Any, value: Any) -> None:
        existed = key in self
        super().__setitem__(key, value)
        if existed:
            if key in self.__order:
                self.__order.move_to_end(key, last=True)
            else:
                self.__order[key] = None
        else:
            self.__order[key] = None

    def __delitem__(self, key: Any) -> None:
        super().__delitem__(key)
        self.__order.pop(key, None)

    def popitem(self):
        if not self.__order:
            raise KeyError("popitem(): cache is empty")
        key, _ = self.__order.popitem(last=False)
        value = super().__getitem__(key)
        super().__delitem__(key)
        return key, value

    def clear(self) -> None:
        super().clear()
        self.__order.clear()