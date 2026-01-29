"""
Cache decorators for functions and methods
"""

import functools
from typing import Any, Callable, Optional, Union

from .keys import hashkey


def cached(cache: Any, key: Callable = hashkey, lock: Any = None):
    """
    Decorator to wrap a function with a memoizing callable that saves
    results in a cache.
    
    Args:
        cache: Cache object implementing dict-like interface
        key: Function to generate cache keys (default: hashkey)
        lock: Optional lock object for thread safety
    """
    def decorator(func):
        if lock is None:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                k = key(*args, **kwargs)
                try:
                    return cache[k]
                except KeyError:
                    pass  # key not found
                v = func(*args, **kwargs)
                try:
                    cache[k] = v
                except ValueError:
                    pass  # value too large
                return v
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                k = key(*args, **kwargs)
                with lock:
                    try:
                        return cache[k]
                    except KeyError:
                        pass  # key not found
                v = func(*args, **kwargs)
                with lock:
                    try:
                        cache[k] = v
                    except ValueError:
                        pass  # value too large
                return v
        return wrapper
    return decorator


class cachedmethod:
    """
    Decorator to wrap a method with a memoizing callable that saves
    results in a cache.
    """
    
    def __init__(self, cache: Any, key: Callable = hashkey, lock: Any = None):
        """
        Initialize cachedmethod decorator.
        
        Args:
            cache: Cache object or callable that returns cache object
            key: Function to generate cache keys (default: hashkey)
            lock: Optional lock object for thread safety
        """
        self.cache = cache
        self.key = key
        self.lock = lock
    
    def __call__(self, method):
        @functools.wraps(method)
        def wrapper(selfobj, *args, **kwargs):
            # Get the cache object
            if callable(self.cache):
                cache = self.cache(selfobj)
            else:
                cache = self.cache
            
            # Generate cache key
            k = self.key(selfobj, *args, **kwargs)
            
            # Try to get from cache
            if self.lock is None:
                try:
                    return cache[k]
                except KeyError:
                    pass  # key not found
            else:
                with self.lock:
                    try:
                        return cache[k]
                    except KeyError:
                        pass  # key not found
            
            # Compute value
            v = method(selfobj, *args, **kwargs)
            
            # Store in cache
            if self.lock is None:
                try:
                    cache[k] = v
                except ValueError:
                    pass  # value too large
            else:
                with self.lock:
                    try:
                        cache[k] = v
                    except ValueError:
                        pass  # value too large
            
            return v
        
        return wrapper