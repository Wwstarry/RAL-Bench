from __future__ import annotations

import functools
from typing import Any, Callable, Optional

from .keys import hashkey, methodkey


_sentinel = object()


def cached(cache, key: Callable[..., Any] = hashkey, lock: Optional[Any] = None):
    """
    Decorator to cache function results in a mapping-like cache.

    lock, if provided, must implement __enter__/__exit__ (e.g., threading.Lock).
    Uses a double-checked pattern and does not hold the lock while calling user code.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            k = key(*args, **kwargs)
            if lock is None:
                try:
                    return cache[k]
                except KeyError:
                    v = func(*args, **kwargs)
                    cache[k] = v
                    return v

            with lock:
                try:
                    return cache[k]
                except KeyError:
                    pass

            v = func(*args, **kwargs)

            with lock:
                # If filled while we computed, return existing.
                try:
                    return cache[k]
                except KeyError:
                    cache[k] = v
                    return v

        wrapper.cache = cache
        wrapper.cache_key = key
        wrapper.cache_lock = lock

        def cache_clear():
            try:
                cache.clear()
            except Exception:
                pass

        wrapper.cache_clear = cache_clear
        return wrapper

    return decorator


def cachedmethod(cache: Callable[..., Any], key: Callable[..., Any] = methodkey, lock: Optional[Any] = None):
    """
    Decorator for methods. `cache(self)` must return a mapping-like cache.

    lock may be None, a lock instance, or a callable lock(self)->lock instance.
    """

    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            c = cache(self)
            l = lock(self) if callable(lock) else lock
            k = key(self, *args, **kwargs)

            if l is None:
                try:
                    return c[k]
                except KeyError:
                    v = method(self, *args, **kwargs)
                    c[k] = v
                    return v

            with l:
                try:
                    return c[k]
                except KeyError:
                    pass

            v = method(self, *args, **kwargs)

            with l:
                try:
                    return c[k]
                except KeyError:
                    c[k] = v
                    return v

        wrapper.cache = cache
        wrapper.cache_key = key
        wrapper.cache_lock = lock
        return wrapper

    return decorator