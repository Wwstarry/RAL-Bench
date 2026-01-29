import functools
from .keys import hashkey

def cached(cache, key=hashkey):
    """Decorator to wrap a function with a memoizing callable that saves
    results in the given cache."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            k = key(*args, **kwargs)
            try:
                return cache[k]
            except KeyError:
                result = func(*args, **kwargs)
                cache[k] = result
                return result
        return wrapper
    return decorator

def cachedmethod(cache, key=hashkey):
    """Decorator to wrap a method with a memoizing callable that saves
    results in the given cache. The cache is shared across all instances."""
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            k = key(self, *args, **kwargs)
            try:
                return cache[k]
            except KeyError:
                result = method(self, *args, **kwargs)
                cache[k] = result
                return result
        return wrapper
    return decorator