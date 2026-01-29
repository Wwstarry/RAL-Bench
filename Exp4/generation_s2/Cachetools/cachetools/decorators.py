from __future__ import annotations

import functools
from typing import Any, Callable, Optional

from .keys import hashkey, methodkey


def cached(
    cache: Any,
    key: Callable[..., Any] = hashkey,
    lock: Optional[Any] = None,
    info: bool = False,
):
    """
    Decorator for caching function results in a cache object.

    Parameters:
      cache: a mutable mapping or a callable returning one.
      key: key function called as key(*args, **kwargs).
      lock: optional lock providing __enter__/__exit__ (e.g. threading.RLock).
    """

    def decorator(func: Callable):
        _cache = cache  # may be mapping or callable

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            c = _cache() if callable(_cache) and not hasattr(_cache, "__getitem__") else _cache
            k = key(*args, **kwargs)
            if lock is None:
                try:
                    return c[k]
                except KeyError:
                    v = func(*args, **kwargs)
                    c[k] = v
                    return v
            else:
                with lock:
                    try:
                        return c[k]
                    except KeyError:
                        v = func(*args, **kwargs)
                        c[k] = v
                        return v

        def cache_clear():
            c = _cache() if callable(_cache) and not hasattr(_cache, "__getitem__") else _cache
            if lock is None:
                c.clear()
            else:
                with lock:
                    c.clear()

        def cache_info():
            # Minimal compatibility: expose hits/misses if tracked (not tracked here)
            # Provide a stable tuple-like object similar to functools.lru_cache.
            return {"cache": cache}

        wrapper.cache = cache  # type: ignore[attr-defined]
        wrapper.cache_key = key  # type: ignore[attr-defined]
        wrapper.cache_clear = cache_clear  # type: ignore[attr-defined]
        if info:
            wrapper.cache_info = cache_info  # type: ignore[attr-defined]
        return wrapper

    return decorator


def cachedmethod(
    cache: Callable[[Any], Any],
    key: Callable[..., Any] = methodkey,
    lock: Optional[Callable[[Any], Any]] = None,
):
    """
    Decorator for caching instance method results.

    Parameters:
      cache: callable(self) -> mutable mapping
      key: key function called as key(self, *args, **kwargs)
      lock: optional callable(self) -> lock
    """

    def decorator(method: Callable):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            c = cache(self)
            k = key(self, *args, **kwargs)
            if lock is None:
                try:
                    return c[k]
                except KeyError:
                    v = method(self, *args, **kwargs)
                    c[k] = v
                    return v
            else:
                lk = lock(self)
                with lk:
                    try:
                        return c[k]
                    except KeyError:
                        v = method(self, *args, **kwargs)
                        c[k] = v
                        return v

        return wrapper

    return decorator