"""Caching decorators."""

import functools
from .keys import hashkey


def cached(cache, key=hashkey, lock=None, info=False):
    """Decorator to wrap a function with a memoizing callable.
    
    Args:
        cache: A cache object (must support __getitem__, __setitem__, __contains__)
        key: A function to compute cache keys from function arguments
        lock: An optional lock object for thread safety
        info: If True, add cache_info() and cache_clear() methods
    """
    def decorator(func):
        if lock is None:
            def wrapper(*args, **kwargs):
                k = key(*args, **kwargs)
                try:
                    return cache[k]
                except KeyError:
                    pass
                v = func(*args, **kwargs)
                try:
                    cache[k] = v
                except ValueError:
                    pass  # value too large
                return v
        else:
            def wrapper(*args, **kwargs):
                k = key(*args, **kwargs)
                try:
                    with lock:
                        return cache[k]
                except KeyError:
                    pass
                v = func(*args, **kwargs)
                try:
                    with lock:
                        cache[k] = v
                except ValueError:
                    pass  # value too large
                return v

        wrapper.cache = cache
        wrapper.cache_key = key
        
        if info:
            hits = misses = 0
            
            def cache_info():
                nonlocal hits, misses
                return functools._CacheInfo(hits, misses, cache.maxsize, len(cache))
            
            def cache_clear():
                nonlocal hits, misses
                cache.clear()
                hits = misses = 0
            
            # Wrap the wrapper to track hits/misses
            original_wrapper = wrapper
            if lock is None:
                def wrapper(*args, **kwargs):
                    nonlocal hits, misses
                    k = key(*args, **kwargs)
                    try:
                        result = cache[k]
                        hits += 1
                        return result
                    except KeyError:
                        misses += 1
                    v = func(*args, **kwargs)
                    try:
                        cache[k] = v
                    except ValueError:
                        pass
                    return v
            else:
                def wrapper(*args, **kwargs):
                    nonlocal hits, misses
                    k = key(*args, **kwargs)
                    try:
                        with lock:
                            result = cache[k]
                            hits += 1
                            return result
                    except KeyError:
                        misses += 1
                    v = func(*args, **kwargs)
                    try:
                        with lock:
                            cache[k] = v
                    except ValueError:
                        pass
                    return v
            
            wrapper.cache = cache
            wrapper.cache_key = key
            wrapper.cache_info = cache_info
            wrapper.cache_clear = cache_clear
        
        return functools.update_wrapper(wrapper, func)
    
    return decorator


def cachedmethod(cache, key=hashkey, lock=None):
    """Decorator to wrap a class or instance method with a memoizing callable.
    
    Args:
        cache: A function that takes self and returns a cache object
        key: A function to compute cache keys from function arguments
        lock: An optional function that takes self and returns a lock object
    """
    def decorator(method):
        if lock is None:
            def wrapper(self, *args, **kwargs):
                c = cache(self)
                k = key(*args, **kwargs)
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
        else:
            def wrapper(self, *args, **kwargs):
                c = cache(self)
                l = lock(self)
                k = key(*args, **kwargs)
                try:
                    with l:
                        return c[k]
                except KeyError:
                    pass
                v = method(self, *args, **kwargs)
                try:
                    with l:
                        c[k] = v
                except ValueError:
                    pass  # value too large
                return v
        
        return functools.update_wrapper(wrapper, method)
    
    return decorator