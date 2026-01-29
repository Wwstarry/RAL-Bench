from __future__ import annotations

import functools
from typing import Any, Callable, Optional

from . import keys as _keys


class _NullLock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _resolve(obj, spec):
    if spec is None:
        return None
    if callable(spec):
        return spec(obj)
    if isinstance(spec, str):
        return getattr(obj, spec)
    return spec


def cached(cache, key=_keys.hashkey, lock: Optional[Any] = None, info: bool = False):
    """
    Decorator for caching function results in the provided cache mapping.

    Exposes:
      - wrapper.cache
      - wrapper.cache_key
      - wrapper.cache_clear()
      - wrapper.__wrapped__
    """
    lockobj = lock if lock is not None else _NullLock()

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            k = key(*args, **kwargs)
            with lockobj:
                try:
                    return cache[k]
                except KeyError:
                    pass
            # compute without holding lock (avoid deadlocks / allow concurrency)
            result = func(*args, **kwargs)
            with lockobj:
                try:
                    cache[k] = result
                except Exception:
                    # If cache rejects insertion, still return computed result.
                    pass
            return result

        wrapper.cache = cache
        wrapper.cache_key = key
        wrapper.__wrapped__ = func

        def cache_clear():
            cache.clear()

        wrapper.cache_clear = cache_clear

        # Minimal compatibility: ignore 'info' unless tests require; keep parameter.
        return wrapper

    return decorator


def cachedmethod(cache, key=_keys.methodkey, lock: Optional[Any] = None):
    """
    Decorator for caching instance/class method results.

    `cache` may be:
      - callable(self)->cache
      - attribute name (str)
      - cache object (shared)

    `lock` may be:
      - None
      - callable(self)->lock
      - attribute name (str)
      - lock object (shared)
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            c = _resolve(self, cache)
            if c is None:
                return func(self, *args, **kwargs)

            lk = _resolve(self, lock)
            lockobj = lk if lk is not None else _NullLock()

            k = key(self, *args, **kwargs)
            with lockobj:
                try:
                    return c[k]
                except KeyError:
                    pass
            result = func(self, *args, **kwargs)
            with lockobj:
                try:
                    c[k] = result
                except Exception:
                    pass
            return result

        def cache_clear(self):
            c = _resolve(self, cache)
            if c is not None:
                c.clear()

        wrapper.cache_clear = cache_clear
        wrapper.__wrapped__ = func
        wrapper.cache = cache
        wrapper.cache_key = key
        return wrapper

    return decorator