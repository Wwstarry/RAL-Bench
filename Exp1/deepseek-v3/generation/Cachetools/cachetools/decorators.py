import functools
from threading import RLock
from .keys import hashkey


def cached(cache, key=hashkey, lock=None):
    """
    Decorator to wrap a function with a memoizing callable that saves
    results in a cache.
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
                with lock:
                    try:
                        return cache[k]
                    except KeyError:
                        pass
                v = func(*args, **kwargs)
                with lock:
                    try:
                        cache[k] = v
                    except ValueError:
                        pass  # value too large
                return v
        
        return functools.update_wrapper(wrapper, func)
    return decorator


class cachedmethod:
    """
    Decorator to wrap a method with a memoizing callable that saves
    results in a cache.
    """
    
    def __init__(self, cache, key=hashkey, lock=None):
        self.cache = cache
        self.key = key
        self.lock = lock
    
    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if callable(self.cache):
                cache = self.cache(self)
            else:
                cache = self.cache
            
            k = self.key(self, *args, **kwargs)
            
            if self.lock is None:
                try:
                    return cache[k]
                except KeyError:
                    pass
                v = func(self, *args, **kwargs)
                try:
                    cache[k] = v
                except ValueError:
                    pass  # value too large
                return v
            else:
                with self.lock:
                    try:
                        return cache[k]
                    except KeyError:
                        pass
                v = func(self, *args, **kwargs)
                with self.lock:
                    try:
                        cache[k] = v
                    except ValueError:
                        pass  # value too large
                return v
        
        return wrapper