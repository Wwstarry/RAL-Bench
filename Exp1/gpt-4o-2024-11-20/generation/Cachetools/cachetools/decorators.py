# Decorators for caching

from functools import wraps
from .keys import hashkey

def cached(cache, key=hashkey):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
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

def cachedmethod(cache_getter, key=hashkey):
    """Decorator to cache method results."""
    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            cache = cache_getter(self)
            k = key(*args, **kwargs)
            try:
                return cache[k]
            except KeyError:
                result = method(self, *args, **kwargs)
                cache[k] = result
                return result
        return wrapper
    return decorator