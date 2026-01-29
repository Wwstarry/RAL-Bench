"""Key function helpers compatible with cachetools' core API.

Only a subset is implemented, sufficient for common use and the test suite.
"""

from __future__ import annotations


# unique marker separating args from kwargs in the generated key tuple
_KW_MARKER = object()


class _HashedTuple(tuple):
    """A tuple subclass that caches its hash.

    Note: tuple subclasses cannot define non-empty __slots__ in CPython.
    We store the cached hash in the instance __dict__ (tuple subclasses
    are allowed to have one unless __slots__=() is set).
    """

    def __hash__(self):
        h = self.__dict__.get("_hash")
        if h is None:
            h = tuple.__hash__(self)
            self.__dict__["_hash"] = h
        return h


def _make_key(args, kwargs, typed: bool):
    if kwargs:
        items = tuple(sorted(kwargs.items()))
        key = args + (_KW_MARKER,) + items
        if typed:
            key = key + tuple(map(type, args)) + tuple(type(v) for _, v in items)
    else:
        key = args
        if typed:
            key = key + tuple(map(type, args))
    return _HashedTuple(key)


def hashkey(*args, **kwargs):
    """Return a hashable key for the given arguments.

    Keyword arguments are normalized by sorting, making order irrelevant.
    """
    return _make_key(args, kwargs, typed=False)


def typedkey(*args, **kwargs):
    """Like hashkey, but include argument types to avoid collisions."""
    return _make_key(args, kwargs, typed=True)


def methodkey(self, *args, **kwargs):
    """Default key function for cachedmethod: ignore self."""
    return hashkey(*args, **kwargs)


def typedmethodkey(self, *args, **kwargs):
    """Typed variant of methodkey."""
    return typedkey(*args, **kwargs)


__all__ = [
    "_HashedTuple",
    "hashkey",
    "typedkey",
    "methodkey",
    "typedmethodkey",
]