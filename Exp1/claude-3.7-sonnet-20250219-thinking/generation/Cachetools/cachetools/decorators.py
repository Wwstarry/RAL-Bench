"""Memoizing function and method decorators."""

import functools
import weakref
from .keys import hashkey, methodkey


class _UnboundMethodProxy:
    """Proxy for an unbound method that helps with cache invalidation."""

    def __init__(self, func, cache, key):
        self.func = func
        self.cache = cache
        self.key = key

    def __call__(self, *args, **kwargs):
        key = self.key(self.func, *args, **kwargs)
        try:
            return self.cache[key]
        except KeyError:
            pass
        value = self.func(*args, **kwargs)
        try:
            self.cache[key] = value
        except ValueError:
            pass
        return value

    def cache_clear(self):
        """Clear the cache and return the number of items removed."""
        count = len(self.cache)
        self.cache.clear()
        return count

    def cache_info(self):
        """Report cache statistics."""
        return {
            'hits': getattr(self.cache, 'hits', 0),
            'misses': getattr(self.cache, 'misses', 0),
            'maxsize': getattr(self.cache, 'maxsize', None),
            'currsize': len(self.cache),
        }


def cached(cache, key=hashkey):
    """Decorator to wrap a function with a memoizing callable.

    Arguments:
        cache: cache object
        key: function to compute cache key from function arguments

    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            k = key(*args, **kwargs)
            try:
                return cache[k]
            except KeyError:
                pass
            value = func(*args, **kwargs)
            try:
                cache[k] = value
            except ValueError:
                pass
            return value

        wrapper.cache = cache
        wrapper.cache_key = key
        wrapper.cache_clear = cache.clear

        def cache_info():
            return {
                'hits': getattr(cache, 'hits', 0),
                'misses': getattr(cache, 'misses', 0),
                'maxsize': getattr(cache, 'maxsize', None),
                'currsize': len(cache),
            }

        wrapper.cache_info = cache_info
        return wrapper
    return decorator


def cachedmethod(cache, key=methodkey):
    """Decorator to wrap a class or instance method with a memoizing callable.

    Arguments:
        cache: cache object or cache factory function
        key: function to compute cache key from function arguments

    """
    def decorator(method):
        if isinstance(cache, type):
            cache_factory = cache
        else:
            def cache_factory():
                return cache

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            c = cache_factory()

            # Try to get cache from instance if not a concrete instance
            if c is None:
                try:
                    c = self.__cache
                except AttributeError:
                    c = self.__cache = {}

            k = key(method, *args, **kwargs)
            try:
                return c[k]
            except KeyError:
                pass
            value = method(self, *args, **kwargs)
            try:
                c[k] = value
            except ValueError:
                pass
            return value

        def clear_cache(self):
            c = cache_factory()
            if c is not None:
                c.clear()
            else:
                try:
                    self.__cache.clear()
                except AttributeError:
                    pass

        wrapper.cache_clear = clear_cache

        # Create an unbound method proxy for access through the class
        proxy = _UnboundMethodProxy(method, cache_factory(), key)
        wrapper._unbound_method = proxy
        wrapper.__get__ = lambda self, obj, objtype=None: (
            proxy if obj is None else functools.partial(wrapper, obj)
        )
        return wrapper
    return decorator