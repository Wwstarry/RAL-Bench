"""Decorator functions for caching."""

import functools
from cachetools.keys import hashkey, methodkey


def cached(cache, key=hashkey):
    """Decorator to wrap a function with a memoizing callable that saves
    results in a cache.
    
    Args:
        cache: A cache object (dict-like with __setitem__, __getitem__, __contains__).
        key: A callable that generates cache keys from function arguments.
              Defaults to hashkey.
    
    Returns:
        A decorator function.
    """
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
        
        wrapper.cache = cache
        return wrapper
    
    return decorator


def cachedmethod(cache, key=methodkey):
    """Decorator to wrap a method with a memoizing callable that saves
    results in a cache stored as an instance attribute.
    
    Args:
        cache: A callable that returns the cache object from self.
               Can be a string (attribute name) or callable.
        key: A callable that generates cache keys from method arguments.
             Defaults to methodkey.
    
    Returns:
        A decorator function.
    """
    def decorator(func):
        if isinstance(cache, str):
            cache_attr = cache
            
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                c = getattr(self, cache_attr)
                k = key(self, *args, **kwargs)
                try:
                    return c[k]
                except KeyError:
                    result = func(self, *args, **kwargs)
                    c[k] = result
                    return result
        else:
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                c = cache(self)
                k = key(self, *args, **kwargs)
                try:
                    return c[k]
                except KeyError:
                    result = func(self, *args, **kwargs)
                    c[k] = result
                    return result
        
        wrapper.cache = cache
        return wrapper
    
    return decorator