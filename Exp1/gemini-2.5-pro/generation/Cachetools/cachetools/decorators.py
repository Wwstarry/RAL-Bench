import functools
from threading import RLock

from . import keys
from .cache import LRUCache


def cached(cache, key=keys.hashkey, lock=None):
    """Decorator to wrap a function with a memoizing callable that saves
    results in a cache.
    """
    # Support @cached syntax
    if callable(cache):
        return cached(LRUCache(maxsize=128), key=keys.hashkey, lock=None)(cache)

    def decorator(func):
        if lock is None:
            _lock = RLock()
        else:
            _lock = lock

        hits = misses = 0

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal hits, misses
            k = key(*args, **kwargs)
            if k is None:
                return func(*args, **kwargs)
            
            try:
                with _lock:
                    result = cache[k]
                hits += 1
                return result
            except KeyError:
                pass  # Fall through to call the function

            result = func(*args, **kwargs)

            with _lock:
                try:
                    cache[k] = result
                    misses += 1
                except ValueError:
                    # cache may be full and we can't evict
                    misses += 1  # still a miss
            return result

        def cache_info():
            """Report cache statistics"""
            with _lock:
                return (hits, misses, cache.maxsize, cache.currsize)

        def cache_clear():
            """Clear the cache and cache statistics"""
            nonlocal hits, misses
            with _lock:
                cache.clear()
                hits = misses = 0

        wrapper.cache_info = cache_info
        wrapper.cache_clear = cache_clear
        return wrapper

    return decorator


def cachedmethod(cache, key=keys.hashkey, lock=None):
    """Decorator to wrap a class method with a memoizing callable that saves
    results in a cache.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            c = cache(self)
            if lock:
                l = lock(self)
            else:
                # Create a lock on the instance if it doesn't exist
                try:
                    l = self.__dict__['_%s_lock' % func.__name__]
                except KeyError:
                    l = self.__dict__.setdefault('_%s_lock' % func.__name__, RLock())

            k = key(*args, **kwargs)
            if k is None:
                return func(self, *args, **kwargs)

            try:
                with l:
                    return c[k]
            except KeyError:
                pass

            result = func(self, *args, **kwargs)
            with l:
                try:
                    c[k] = result
                except ValueError:
                    pass  # cache full
            return result

        return wrapper
    return decorator