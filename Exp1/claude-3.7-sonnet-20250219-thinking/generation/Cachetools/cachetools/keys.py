"""Key functions for memoizing decorators."""

import functools
import inspect
import operator
import types


class _HashedKey(list):
    """A hashable list of unhashable objects."""
    __slots__ = ()

    def __hash__(self):
        return hash(tuple(map(id, self)))


def hashkey(*args, **kwargs):
    """Return a cache key for the specified hashable arguments."""
    return (args, frozenset(kwargs.items()))


def methodkey(method, *args, **kwargs):
    """Return a cache key for a method call."""
    return (method.__self__, method.__func__, args, frozenset(kwargs.items()))


def typedkey(*args, **kwargs):
    """Return a typed cache key for the specified arguments."""
    key = hashkey(*args, **kwargs)
    key += tuple(type(arg) for arg in args)
    key += tuple((name, type(value)) for name, value in kwargs.items())
    return key