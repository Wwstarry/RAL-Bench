from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Optional

from .keys import hashkey, methodkey


def cached(cache, key: Callable[..., Any] = hashkey, lock=None, info=False):
    """
    Decorator to memoize a function using the given cache.

    Parameters:
      cache: a MutableMapping-like object (typically Cache/LRUCache/TTLCache)
      key: function that maps (*args, **kwargs) -> hashable key
      lock: optional lock with __enter__/__exit__ (e.g., threading.RLock)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            k = key(*args, **kwargs)
            if lock is None:
                try:
                    return cache[k]
                except KeyError:
                    v = func(*args, **kwargs)
                    cache[k] = v
                    return v
            else:
                with lock:
                    try:
                        return cache[k]
                    except KeyError:
                        v = func(*args, **kwargs)
                        cache[k] = v
                        return v

        # minimal compatibility attributes used by some tests
        wrapper.cache = cache
        wrapper.cache_key = key
        wrapper.cache_lock = lock
        return wrapper

    return decorator


def cachedmethod(cache, key: Callable[..., Any] = methodkey, lock: Optional[Callable[[Any], Any]] = None):
    """
    Decorator for instance/class methods where `cache` is a callable
    returning the cache for the instance (or the cache object itself).

    cache: callable(self) -> mapping OR mapping
    key: function(self, *args, **kwargs) -> hashable key (default ignores self)
    lock: optional callable(self) -> context manager lock
    """
    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            c = cache(self) if callable(cache) else cache
            k = key(self, *args, **kwargs)

            cm = None
            if lock is not None:
                cm = lock(self) if callable(lock) else lock

            if cm is None:
                try:
                    return c[k]
                except KeyError:
                    v = method(self, *args, **kwargs)
                    c[k] = v
                    return v
            else:
                with cm:
                    try:
                        return c[k]
                    except KeyError:
                        v = method(self, *args, **kwargs)
                        c[k] = v
                        return v

        wrapper.cache = cache
        wrapper.cache_key = key
        wrapper.cache_lock = lock
        return wrapper

    return decorator