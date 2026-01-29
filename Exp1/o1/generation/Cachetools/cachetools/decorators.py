from functools import wraps
from .keys import hashkey, methodkey

def cached(cache, key=hashkey, lock=None):
    """
    Decorator that wraps a function with a memoizing callable
    that saves results in a given cache object.
    """
    def decorator(func):
        if lock is None:
            @wraps(func)
            def wrapper(*args, **kwargs):
                k = key(*args, **kwargs)
                try:
                    return cache[k]
                except KeyError:
                    result = func(*args, **kwargs)
                    cache[k] = result
                    return result
        else:
            from threading import Lock
            if lock is True:
                cache_lock = Lock()
            else:
                cache_lock = lock

            @wraps(func)
            def wrapper(*args, **kwargs):
                k = key(*args, **kwargs)
                with cache_lock:
                    try:
                        return cache[k]
                    except KeyError:
                        result = func(*args, **kwargs)
                        cache[k] = result
                        return result
        return wrapper
    return decorator

def cachedmethod(cache, key=methodkey, lock=None):
    """
    Decorator for methods that memoizes results in a cache object
    returned by cache(self). key is used to build a cache key from
    (self, *args, **kwargs).
    """
    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            c = cache(self)
            if c is None:
                return method(self, *args, **kwargs)
            k = key(self, *args, **kwargs)
            if lock is None:
                try:
                    return c[k]
                except KeyError:
                    result = method(self, *args, **kwargs)
                    c[k] = result
                    return result
            else:
                from threading import Lock
                if lock is True:
                    cache_lock = Lock()
                else:
                    cache_lock = lock

                with cache_lock:
                    try:
                        return c[k]
                    except KeyError:
                        result = method(self, *args, **kwargs)
                        c[k] = result
                        return result
        return wrapper
    return decorator