"""
Core cache classes.

Only a subset of the behaviour of the original ‘cachetools’ is implemented.
The focus lies on functional parity for the accompanying test-suites rather
than *all* bells and whistles.
"""
from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import MutableMapping
from typing import Any, Callable, Iterator, Tuple, Optional


# --------------------------------------------------------------------------- #
# Helper                                                                      #
# --------------------------------------------------------------------------- #
def _default_getsizeof(obj: Any, _default: int = 1) -> int:
    """
    Fallback for `getsizeof` – counts entries, not memory.
    """
    return _default


class Cache(MutableMapping):
    """
    Dictionary-like cache with a configurable *maxsize* and *getsizeof*
    callable (default: each entry has a size of 1).

    Sub-classes are responsible for implementing the `__setitem__` logic that
    handles eviction once `maxsize` would be exceeded.
    """

    def __init__(
        self,
        maxsize: Optional[int] = 128,
        *,
        getsizeof: Optional[Callable[[Any], int]] = None,
    ):
        if maxsize is not None and maxsize < 0:
            raise ValueError("maxsize must be >= 0 or None")
        self.maxsize: Optional[int] = maxsize
        self.getsizeof: Callable[[Any], int] = getsizeof or _default_getsizeof
        self._Cache__data: dict[Any, Any] = {}
        self._Cache__currsize: int = 0

    # -------------- mapping protocol ------------------------------------- #
    def __len__(self) -> int:  # noqa: D401
        return len(self._Cache__data)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._Cache__data)

    def __contains__(self, key: Any) -> bool:
        return key in self._Cache__data

    def __getitem__(self, key: Any):
        try:
            return self._Cache__data[key]
        except KeyError:
            raise

    def __setitem__(self, key: Any, value: Any) -> None:  # pragma: no cover
        """
        Base implementation – stores the item and updates `currsize` without
        eviction.  Sub-classes are expected to override this to add eviction
        policies.  We still keep a basic implementation such that `Cache`
        alone works as an unbounded mapping with *optional* size tracking.
        """
        old_size = self.getsizeof(self._Cache__data.get(key, None)) if key in self._Cache__data else 0
        new_size = self.getsizeof(value)
        self._Cache__data[key] = value
        self._Cache__currsize += new_size - old_size
        if self.maxsize is not None and self._Cache__currsize > self.maxsize:
            # Eject arbitrary item (FIFO) – maintaining insertion order.
            k, v = self._Cache__data.popitem(last=False) if isinstance(self._Cache__data, OrderedDict) else self._Cache__data.popitem()
            self._Cache__currsize -= self.getsizeof(v)
            # Equivalent behaviour to reference: raise CacheKeyError?  We skip.

    def __delitem__(self, key: Any) -> None:
        value = self._Cache__data.pop(key)
        self._Cache__currsize -= self.getsizeof(value)

    # Properties & helpers -------------------------------------------------- #
    @property
    def currsize(self) -> int:
        return self._Cache__currsize

    def get(self, key: Any, default: Any = None):
        try:
            return self[key]
        except KeyError:
            return default

    def popitem(self) -> Tuple[Any, Any]:
        """
        Remove and return a `(key, value)` pair.  Sub-classes may choose which
        item to remove based on their eviction policy.  The base version removes
        an arbitrary element.
        """
        key, value = self._Cache__data.popitem()
        self._Cache__currsize -= self.getsizeof(value)
        return key, value

    # For representation
    def __repr__(self) -> str:
        classname = self.__class__.__name__
        return f"{classname}({self._Cache__data})"


class LRUCache(Cache):
    """
    A least-recently-used cache.  Accessing an item refreshes its position.
    """

    def __init__(
        self,
        maxsize: int = 128,
        *,
        getsizeof: Optional[Callable[[Any], int]] = None,
    ):
        if maxsize is not None and maxsize < 1:
            raise ValueError("maxsize should be at least 1")
        super().__init__(maxsize, getsizeof=getsizeof)
        # we need an ordered dictionary to track usage
        self._Cache__data = OrderedDict()

    # -------------- mapping protocol overrides ---------------------------- #
    def __getitem__(self, key: Any):
        try:
            value = self._Cache__data.pop(key)
        except KeyError:  # not in cache
            raise
        # Re-insert at the end (most recently used)
        self._Cache__data[key] = value
        return value

    def __setitem__(self, key: Any, value: Any) -> None:
        size = self.getsizeof(value)
        # If key exists, remove first to update size and position.
        if key in self._Cache__data:
            old_value = self._Cache__data.pop(key)
            self._Cache__currsize -= self.getsizeof(old_value)

        self._Cache__data[key] = value  # insert at end
        self._Cache__currsize += size

        # Evict while above capacity
        if self.maxsize is not None:
            while self._Cache__currsize > self.maxsize and self._Cache__data:
                k, v = self._Cache__data.popitem(last=False)  # LRU = first
                self._Cache__currsize -= self.getsizeof(v)


class TTLCache(LRUCache):
    """
    A least-recently-used cache with per-item time-to-live expiration.
    """

    def __init__(
        self,
        maxsize: int = 128,
        ttl: int | float = 600,
        *,
        timer: Callable[[], float] = time.monotonic,
        getsizeof: Optional[Callable[[Any], int]] = None,
    ):
        if ttl <= 0:
            raise ValueError("ttl must be > 0")
        super().__init__(maxsize, getsizeof=getsizeof)
        self.ttl: float = float(ttl)
        self.timer: Callable[[], float] = timer

    # -------------- internal helpers -------------------------------------- #
    def _expire(self) -> None:
        """
        Purge expired items starting from the least recently used side until
        the first non-expired item is encountered.
        """
        if not self._Cache__data:
            return
        now = self.timer()
        # OrderedDict is ordered by usage (LRU first)
        keys_to_delete = []
        for k, (exp, _val) in self._Cache__data.items():
            if exp < now:
                keys_to_delete.append(k)
            else:
                # Stop at the first non-expired (they are ordered by usage, not exp time,
                # but we still break to keep O(N) in number of expired at front).
                break
        for k in keys_to_delete:
            v_tuple = self._Cache__data.pop(k)
            self._Cache__currsize -= self.getsizeof(v_tuple[1])  # size of stored value

    def __contains__(self, key: Any) -> bool:
        try:
            value = self.__getitem__(key)
        except KeyError:
            return False
        return True

    # -------------- mapping protocol overrides ---------------------------- #
    def __getitem__(self, key: Any):
        self._expire()
        exp, val = super().__getitem__(key)  # This also moves to end
        if exp < self.timer():
            # expired right after moving; evict and raise KeyError
            super().__delitem__(key)
            raise KeyError(key)
        return val

    def __setitem__(self, key: Any, value: Any) -> None:
        self._expire()
        expire_at = self.timer() + self.ttl
        super().__setitem__(key, (expire_at, value))

    def get(self, key: Any, default: Any = None):
        try:
            return self[key]
        except KeyError:
            return default

    def __iter__(self) -> Iterator[Any]:
        self._expire()
        # Need to yield keys in LRU order (oldest ‑> newest) as per OrderedDict
        for key in list(self._Cache__data.keys()):
            try:
                yield key  # __getitem__ side-effect will move to end
            except KeyError:
                # Item might have expired and been purged by __getitem__
                continue

    def items(self):
        self._expire()
        for k in list(self._Cache__data.keys()):
            try:
                yield (k, self[k])
            except KeyError:
                continue