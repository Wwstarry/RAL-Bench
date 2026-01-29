"""
Decorators for function and method caching.
"""
from __future__ import annotations

import threading
from functools import wraps
from operator import attrgetter
from typing import Callable, Any, Mapping

from .keys import hashkey


def _determine_cache(cache):
    """
    Accept either an actual mapping or a zero-arg callable returning a mapping.
    """
    if callable(cache) and not isinstance(cache, Mapping):
        return cache  # will be called later
    else:
        return lambda: cache


def cached(cache, key: Callable[..., Any] | None = None, lock: threading.Lock | None = None):
    """
    Decorator to cache *function* calls.

    Parameters:
        cache: Mapping or callable returning a mapping.  Must support the
               ``__getitem__``/``__setitem__`` protocol (e.g. LRUCache()).
        key:   Callable used to create a cache-key.  If *None*, defaults to
               ``cachetools.keys.hashkey``.
        lock:  Optional threading.Lock or compatible object providing
               ``acquire``/``release`` – for thread safety.
    """

    key_fn = key or hashkey
    cache_factory = _determine_cache(cache)
    lock_obj = lock or threading.RLock()

    def decorator(user_func: Callable):
        cache_instance = None  # closed-over variable

        @wraps(user_func)
        def wrapper(*args, **kwargs):
            nonlocal cache_instance
            if cache_instance is None:
                cache_instance = cache_factory()

            k = key_fn(*args, **kwargs)
            with lock_obj:
                try:
                    return cache_instance[k]
                except KeyError:
                    pass  # compute value below

            result = user_func(*args, **kwargs)

            with lock_obj:
                # race condition possible but acceptable for simple impl
                cache_instance[k] = result
            return result

        wrapper.cache = lambda: cache_instance  # type: ignore
        return wrapper

    return decorator


def cachedmethod(
    cache: Callable[[Any], Mapping] | str = attrgetter("__cache__"),
    key: Callable[..., Any] | None = None,
    lock: threading.Lock | Callable[[Any], threading.Lock] | None = None,
):
    """
    Decorator similar to `cached` but intended for *instance* or *class*
    methods where the cache lives on the object itself.

    By default the cache is expected to be available via `self.__cache__`.
    """

    key_fn = key or hashkey

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Resolve cache instance
            cache_obj = cache(self) if callable(cache) else getattr(self, cache)
            if cache_obj is None:
                # Lazily create if the attribute is a factory
                cache_obj = cache_obj() if callable(cache_obj) else cache_obj

            # Resolve lock (may be a callable on self)
            lock_obj = None
            if lock is None:
                lock_obj = None
            elif callable(lock):
                lock_obj = lock(self)
            else:
                lock_obj = lock

            k = key_fn(*args, **kwargs)  # self not included in key per cachetools

            try:
                if lock_obj:
                    lock_obj.acquire()
                return cache_obj[k]
            except KeyError:
                pass
            finally:
                if lock_obj:
                    lock_obj.release()

            result = func(self, *args, **kwargs)

            try:
                if lock_obj:
                    lock_obj.acquire()
                cache_obj[k] = result
            finally:
                if lock_obj:
                    lock_obj.release()
            return result

        return wrapper

    return decorator