from typing import Callable, Any
from functools import wraps

from .keys import hashkey


def cached(cache, key: Callable | None = hashkey, lock: Any | None = None):
    """
    Decorator to cache function calls using the given cache.

    cache: a mapping-like object supporting __getitem__/__setitem__ OR a
           callable that returns such a mapping when invoked.
    key: a key-building function; defaults to cachetools.keys.hashkey.
    lock: optional threading.Lock-like object with acquire/release; if provided
          it is used to guard cache access.
    """
    def decorator(func):
        kfunc = key or hashkey

        @wraps(func)
        def wrapper(*args, **kwargs):
            k = kfunc(*args, **kwargs)
            c = cache() if callable(cache) else cache
            if lock is not None:
                lock.acquire()
            try:
                try:
                    return c[k]
                except KeyError:
                    result = func(*args, **kwargs)
                    c[k] = result
                    return result
            finally:
                if lock is not None:
                    lock.release()

        return wrapper

    return decorator


def cachedmethod(cache, key: Callable | None = hashkey, lock: Any | None = None):
    """
    Decorator to cache instance method calls, supporting per-instance caches.

    cache: either a mapping-like object (shared across instances) or a callable
           taking the bound instance (self) and returning a mapping-like cache.
    key: a key function; defaults to cachetools.keys.hashkey. The bound instance
         (self) is included in the key arguments by default to avoid collisions.
    lock: optional lock used to guard cache accesses.
    """
    def decorator(method):
        kfunc = key or hashkey

        @wraps(method)
        def wrapper(self, *args, **kwargs):
            # include self in key by default
            try:
                k = kfunc(self, *args, **kwargs)
            except TypeError:
                # fall back: some key funcs may not accept self; then exclude it
                k = kfunc(*args, **kwargs)
            c = cache(self) if callable(cache) else cache
            if lock is not None:
                lock.acquire()
            try:
                try:
                    return c[k]
                except KeyError:
                    result = method(self, *args, **kwargs)
                    c[k] = result
                    return result
            finally:
                if lock is not None:
                    lock.release()

        return wrapper

    return decorator