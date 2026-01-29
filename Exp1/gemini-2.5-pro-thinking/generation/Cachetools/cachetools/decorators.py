"""Decorators for memoizing function and method calls."""

import collections
import functools
from threading import RLock

from . import keys


def cached(cache, key=keys.hashkey, lock=None):
    """Decorator to wrap a function with a memoizing callable that saves
    results in a cache.
    """
    # Handle bare decorator usage: @cached
    if callable(cache):
        func = cache
        return cached(cache={}, key=keys.hashkey, lock=None)(func)

    def decorator(func):
        _lock = lock
        if _lock is None:
            _lock = RLock()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            k = key(*args, **kwargs)
            try:
                return cache[k]
            except KeyError:
                pass  # key not found

            with _lock:
                try:
                    return cache[k]  # double-check
                except KeyError:
                    pass  # fall through to call the function

                v = func(*args, **kwargs)
                try:
                    cache[k] = v
                except ValueError:
                    pass  # value too large for cache
                return v

        def cache_clear():
            """Clear the cache."""
            with _lock:
                cache.clear()

        def cache_info():
            """Report cache statistics."""
            # This is a simplified version for API compatibility.
            # It doesn't track hits/misses.
            CacheInfo = collections.namedtuple(
                'CacheInfo', ['hits', 'misses', 'maxsize', 'currsize']
            )
            return CacheInfo(
                hits=None,
                misses=None,
                maxsize=getattr(cache, 'maxsize', None),
                currsize=getattr(cache, 'currsize', len(cache))
            )

        wrapper.cache = cache
        wrapper.key = key
        wrapper.lock = _lock
        wrapper.cache_clear = cache_clear
        wrapper.cache_info = cache_info

        return wrapper

    return decorator


def cachedmethod(cache, key=keys.hashkey, lock=None):
    """Decorator to wrap a class method with a memoizing callable that saves
    results in a cache specific to each instance.
    """
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            c = cache(self)
            if lock:
                l = lock(self)
            else:
                try:
                    l = self._cache_lock
                except AttributeError:
                    l = self._cache_lock = RLock()

            k = key(self, *args, **kwargs)
            try:
                return c[k]
            except KeyError:
                pass

            with l:
                try:
                    return c[k]
                except KeyError:
                    pass

                v = method(self, *args, **kwargs)
                try:
                    c[k] = v
                except ValueError:
                    pass  # value too large
                return v

        def cache_clear(self):
            """Clear the instance's cache."""
            cache(self).clear()

        def cache_info(self):
            """Report cache statistics for the instance."""
            c = cache(self)
            CacheInfo = collections.namedtuple(
                'CacheInfo', ['hits', 'misses', 'maxsize', 'currsize']
            )
            return CacheInfo(
                hits=None,
                misses=None,
                maxsize=getattr(c, 'maxsize', None),
                currsize=getattr(c, 'currsize', len(c))
            )

        wrapper.cache = cache
        wrapper.key = key
        wrapper.lock = lock
        wrapper.cache_clear = cache_clear
        wrapper.cache_info = cache_info

        return wrapper
    return decorator