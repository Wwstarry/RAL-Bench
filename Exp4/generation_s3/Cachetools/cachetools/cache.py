from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Iterable, Iterator, MutableMapping
from typing import Any, Callable, Dict, Hashable, Optional, Tuple


_sentinel = object()


def _default_getsizeof(value: Any) -> int:
    return 1


class Cache(MutableMapping):
    """
    Base cache implementing a sizing/eviction framework with dict-like semantics.

    Subclasses implement eviction policy by overriding `popitem()`.
    """

    def __init__(self, maxsize: Optional[int], getsizeof: Optional[Callable[[Any], int]] = None):
        self._Cache__data: Dict[Hashable, Any] = {}
        self._Cache__size: Dict[Hashable, int] = {}
        self._Cache__currsize: int = 0

        self._maxsize = maxsize
        self._getsizeof = getsizeof

    @property
    def maxsize(self) -> Optional[int]:
        return self._maxsize

    @property
    def currsize(self) -> int:
        return self._Cache__currsize

    @property
    def getsizeof(self) -> Optional[Callable[[Any], int]]:
        return self._getsizeof

    # ---- internal helpers ----
    def _sizeof(self, value: Any) -> int:
        fn = self._getsizeof
        if fn is None:
            s = 1
        else:
            s = fn(value)
        # avoid weirdness with <=0 sizes
        try:
            if s <= 0:
                s = 1
        except TypeError:
            s = 1
        return int(s)

    def _recalc_currsize(self) -> None:
        self._Cache__currsize = sum(self._Cache__size.values())

    def _ensure_capacity(self) -> None:
        # evict until within bounds; must not infinite-loop
        if self._maxsize is None:
            return
        maxsize = self._maxsize
        if maxsize < 0:
            # treat negative as 0-ish
            maxsize = 0
        while self._Cache__currsize > maxsize and len(self._Cache__data):
            self.popitem()
        # If still oversize and empty, we're done.

    # ---- MutableMapping API ----
    def __len__(self) -> int:
        return len(self._Cache__data)

    def __iter__(self) -> Iterator:
        return iter(self._Cache__data)

    def __contains__(self, key: object) -> bool:
        return key in self._Cache__data

    def __getitem__(self, key: Hashable) -> Any:
        return self._Cache__data[key]

    def __setitem__(self, key: Hashable, value: Any) -> None:
        size = self._sizeof(value)
        data = self._Cache__data
        sizes = self._Cache__size

        if key in data:
            oldsize = sizes.get(key, 0)
            data[key] = value
            sizes[key] = size
            self._Cache__currsize += (size - oldsize)
        else:
            data[key] = value
            sizes[key] = size
            self._Cache__currsize += size

        self._ensure_capacity()

    def __delitem__(self, key: Hashable) -> None:
        data = self._Cache__data
        sizes = self._Cache__size
        if key not in data:
            raise KeyError(key)
        del data[key]
        self._Cache__currsize -= sizes.pop(key, 0)

    def pop(self, key: Hashable, default: Any = _sentinel) -> Any:
        if key in self._Cache__data:
            value = self._Cache__data.pop(key)
            self._Cache__currsize -= self._Cache__size.pop(key, 0)
            return value
        if default is _sentinel:
            raise KeyError(key)
        return default

    def get(self, key: Hashable, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def clear(self) -> None:
        self._Cache__data.clear()
        self._Cache__size.clear()
        self._Cache__currsize = 0

    def setdefault(self, key: Hashable, default: Any = None) -> Any:
        if key in self:
            return self[key]
        self[key] = default
        return default

    def update(self, *args, **kwargs) -> None:
        if args:
            if len(args) > 1:
                raise TypeError(f"update expected at most 1 argument, got {len(args)}")
            other = args[0]
            if isinstance(other, MutableMapping) or hasattr(other, "items"):
                for k, v in other.items():
                    self[k] = v
            else:
                for k, v in other:
                    self[k] = v
        for k, v in kwargs.items():
            self[k] = v

    def keys(self):
        return self._Cache__data.keys()

    def items(self):
        return self._Cache__data.items()

    def values(self):
        return self._Cache__data.values()

    def popitem(self) -> Tuple[Hashable, Any]:
        """
        Remove and return an arbitrary (key, value) pair.

        Subclasses should override to implement a deterministic eviction policy.
        """
        if not self._Cache__data:
            raise KeyError("cache is empty")
        # default: FIFO-ish based on dict insertion order
        key = next(iter(self._Cache__data))
        value = self._Cache__data.pop(key)
        self._Cache__currsize -= self._Cache__size.pop(key, 0)
        return key, value

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(maxsize={self._maxsize!r}, currsize={self.currsize!r}, items={dict(self._Cache__data)!r})"


class LRUCache(Cache):
    """
    Least-recently-used cache.

    Recency is updated on successful __getitem__ and get() hits, and on __setitem__.
    """

    def __init__(self, maxsize: Optional[int], getsizeof: Optional[Callable[[Any], int]] = None):
        super().__init__(maxsize, getsizeof=getsizeof)
        self._LRU__order: "OrderedDict[Hashable, None]" = OrderedDict()

    def __len__(self) -> int:
        return len(self._LRU__order)

    def __iter__(self) -> Iterator:
        return iter(self._LRU__order)

    def __contains__(self, key: object) -> bool:
        # Do not update recency on containment checks.
        return key in self._LRU__order

    def _touch(self, key: Hashable) -> None:
        od = self._LRU__order
        if key in od:
            od.move_to_end(key, last=True)

    def __getitem__(self, key: Hashable) -> Any:
        value = super().__getitem__(key)
        self._touch(key)
        return value

    def get(self, key: Hashable, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key: Hashable, value: Any) -> None:
        existed = key in self._LRU__order
        super().__setitem__(key, value)
        # Ensure order bookkeeping reflects actual presence after potential evictions.
        od = self._LRU__order
        if key in self:  # still present after eviction
            if existed:
                od.move_to_end(key, last=True)
            else:
                od[key] = None
                od.move_to_end(key, last=True)
        # Remove any keys from order that were evicted by base eviction loop.
        # (Base uses popitem overridden here, so normally consistent; but keep robust.)
        stale = [k for k in od.keys() if k not in super().keys()]
        for k in stale:
            od.pop(k, None)

    def __delitem__(self, key: Hashable) -> None:
        super().__delitem__(key)
        self._LRU__order.pop(key, None)

    def pop(self, key: Hashable, default: Any = _sentinel) -> Any:
        if key in self:
            self._LRU__order.pop(key, None)
        return super().pop(key, default)

    def clear(self) -> None:
        super().clear()
        self._LRU__order.clear()

    def popitem(self) -> Tuple[Hashable, Any]:
        if not self._LRU__order:
            raise KeyError("cache is empty")
        key, _ = self._LRU__order.popitem(last=False)  # LRU
        value = super().pop(key)
        return key, value


class TTLCache(Cache):
    """
    Cache with per-item TTL (time-to-live) expiration plus LRU eviction among live items.
    TTL is refreshed on __setitem__ only (not on access).
    """

    def __init__(
        self,
        maxsize: Optional[int],
        ttl: float,
        timer: Callable[[], float] = time.monotonic,
        getsizeof: Optional[Callable[[Any], int]] = None,
    ):
        super().__init__(maxsize, getsizeof=getsizeof)
        self._TTL__ttl = float(ttl)
        self._TTL__timer = timer
        self._TTL__expires: Dict[Hashable, float] = {}
        self._TTL__order: "OrderedDict[Hashable, None]" = OrderedDict()

    @property
    def ttl(self) -> float:
        return self._TTL__ttl

    @property
    def timer(self) -> Callable[[], float]:
        return self._TTL__timer

    def _now(self) -> float:
        return float(self._TTL__timer())

    def expire(self, time: Optional[float] = None):
        """
        Remove expired items.

        Returns a list of (key, value) removed (compatible enough for most uses).
        """
        now = self._now() if time is None else float(time)
        expired_keys = [k for k, exp in list(self._TTL__expires.items()) if exp <= now]
        removed = []
        for k in expired_keys:
            if k in self:
                try:
                    v = super().pop(k)
                except KeyError:
                    v = None
                removed.append((k, v))
            self._TTL__expires.pop(k, None)
            self._TTL__order.pop(k, None)
        return removed

    def _is_expired(self, key: Hashable, now: Optional[float] = None) -> bool:
        exp = self._TTL__expires.get(key)
        if exp is None:
            return False
        n = self._now() if now is None else now
        return exp <= n

    def _purge_if_expired(self, key: Hashable) -> bool:
        if key in self._TTL__expires and self._is_expired(key):
            # remove entirely
            self._TTL__expires.pop(key, None)
            self._TTL__order.pop(key, None)
            try:
                super().pop(key)
            except KeyError:
                pass
            return True
        return False

    def __len__(self) -> int:
        self.expire()
        return len(self._TTL__order)

    def __iter__(self) -> Iterator:
        self.expire()
        return iter(self._TTL__order)

    def __contains__(self, key: object) -> bool:
        if key not in self._TTL__order:
            return False
        # do not update recency on contains; but must not claim expired
        try:
            self._purge_if_expired(key)  # type: ignore[arg-type]
        except Exception:
            return False
        return key in self._TTL__order

    def __getitem__(self, key: Hashable) -> Any:
        if key not in self._TTL__order:
            raise KeyError(key)
        if self._purge_if_expired(key):
            raise KeyError(key)
        value = super().__getitem__(key)
        # LRU semantics among live entries: access updates recency
        self._TTL__order.move_to_end(key, last=True)
        return value

    def get(self, key: Hashable, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key: Hashable, value: Any) -> None:
        # purge expired globally first so capacity checks consider only live items
        self.expire()
        existed = key in self._TTL__order

        super().__setitem__(key, value)
        # If item still present, record expiry and recency
        if key in self:
            self._TTL__expires[key] = self._now() + self._TTL__ttl
            if existed:
                self._TTL__order.move_to_end(key, last=True)
            else:
                self._TTL__order[key] = None
                self._TTL__order.move_to_end(key, last=True)

        # super().__setitem__ may have evicted entries (via our popitem)
        # Ensure metadata cleaned for any missing keys.
        for k in list(self._TTL__expires.keys()):
            if k not in super().keys():
                self._TTL__expires.pop(k, None)
                self._TTL__order.pop(k, None)
        for k in list(self._TTL__order.keys()):
            if k not in super().keys():
                self._TTL__order.pop(k, None)
                self._TTL__expires.pop(k, None)

    def __delitem__(self, key: Hashable) -> None:
        # deleting an expired item should behave as missing
        if self._purge_if_expired(key):
            raise KeyError(key)
        super().__delitem__(key)
        self._TTL__order.pop(key, None)
        self._TTL__expires.pop(key, None)

    def pop(self, key: Hashable, default: Any = _sentinel) -> Any:
        # treat expired as missing
        self._purge_if_expired(key)
        if key in self._TTL__order:
            self._TTL__order.pop(key, None)
            self._TTL__expires.pop(key, None)
        return super().pop(key, default)

    def clear(self) -> None:
        super().clear()
        self._TTL__expires.clear()
        self._TTL__order.clear()

    def keys(self):
        self.expire()
        return self._TTL__order.keys()

    def items(self):
        self.expire()
        # generate from underlying mapping for current values, in LRU order
        return [(k, super().__getitem__(k)) for k in self._TTL__order.keys()]

    def values(self):
        self.expire()
        return [super().__getitem__(k) for k in self._TTL__order.keys()]

    def popitem(self) -> Tuple[Hashable, Any]:
        # purge expired first
        self.expire()
        if not self._TTL__order:
            raise KeyError("cache is empty")
        key, _ = self._TTL__order.popitem(last=False)  # LRU among live
        self._TTL__expires.pop(key, None)
        value = super().pop(key)
        return key, value