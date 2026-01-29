"""Key functions for memoizing decorators."""

import functools

_sentinel = object()


def hashkey(*args, **kwargs):
    """Return a cache key for the given arguments."""
    key = args
    if kwargs:
        key += (_sentinel,)
        for item in sorted(kwargs.items()):
            key += item
    # This will raise TypeError for unhashable types, which is the
    # expected behavior for the default key function.
    hash(key)
    return key


def typedkey(*args, **kwargs):
    """Return a cache key for the given arguments, including their types."""
    key = hashkey(*args, **kwargs)
    key += tuple(type(v) for v in args)
    key += tuple(type(v) for v in kwargs.values())
    return key