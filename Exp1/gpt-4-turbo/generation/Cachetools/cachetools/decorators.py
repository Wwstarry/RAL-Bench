import functools
from .keys import hashkey

def cached(cache, key=hashkey):
    """Decorator to wrap a function with a memoizing callable using a cache."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            k = key(*args, **kwargs)
            try:
                return cache[k]
            except KeyError:
                v = func(*args, **kwargs)
                cache[k] = v
                return v
        return wrapper
    return decorator

def cachedmethod(cache, key=hashkey):
    """Decorator for caching methods with a cache."""

    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            c = cache(self) if callable(cache) else cache
            k = key(self, *args, **kwargs)
            try:
                return c[k]
            except KeyError:
                v = method(self, *args, **kwargs)
                c[k] = v
                return v
        return wrapper
    return decorator