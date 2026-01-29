"""Key functions for memoizing decorators."""

import collections.abc

_MARKER = object()


def _convert_unhashable(obj):
    if isinstance(obj, collections.abc.Hashable):
        return obj
    if isinstance(obj, collections.abc.Mapping):
        return tuple(sorted((_convert_unhashable(k), _convert_unhashable(v))
                            for k, v in obj.items()))
    if isinstance(obj, collections.abc.Iterable):
        return tuple(_convert_unhashable(i) for i in obj)
    raise TypeError("unhashable type: '%s'" % type(obj).__name__)


def hashkey(*args, **kwargs):
    """Return a cache key for the specified hashable arguments."""
    if not kwargs:
        return args
    try:
        key = args + (_MARKER,) + tuple(sorted(kwargs.items()))
        return key
    except TypeError:
        return None


def typedkey(*args, **kwargs):
    """Return a cache key for the specified arguments.

    The key reflects the types of the arguments.
    """
    try:
        key = hashkey(*args, **kwargs)
        if key is None:
            return None
        key += tuple(type(v) for v in args)
        key += tuple(type(v) for _, v in sorted(kwargs.items()))
        return key
    except TypeError:
        return None