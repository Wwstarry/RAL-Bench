from __future__ import annotations

from typing import Any, Tuple


class _HashedTuple(tuple):
    __slots__ = ("_hash",)

    def __new__(cls, items):
        return super().__new__(cls, items)

    def __init__(self, items):
        self._hash = None

    def __hash__(self):
        h = self._hash
        if h is None:
            h = tuple.__hash__(self)
            self._hash = h
        return h


def _kwmark():
    # unique marker separating args from kwargs
    return object()


_KWMARK = _kwmark()


def hashkey(*args: Any, **kwargs: Any) -> Tuple[Any, ...]:
    """
    Build a hashable cache key from positional and keyword arguments.
    Keyword arguments are sorted by key to provide stable ordering.
    """
    if not kwargs:
        return _HashedTuple(args)
    items = list(args)
    items.append(_KWMARK)
    for k in sorted(kwargs):
        items.append(k)
        items.append(kwargs[k])
    return _HashedTuple(items)


def methodkey(self: Any, *args: Any, **kwargs: Any) -> Tuple[Any, ...]:
    """
    Like hashkey, but ignores `self` for methods.
    """
    return hashkey(*args, **kwargs)


def typedkey(*args: Any, **kwargs: Any) -> Tuple[Any, ...]:
    """
    Like hashkey, but also includes the types of arguments.
    """
    if not kwargs:
        return _HashedTuple(args + tuple(type(v) for v in args))
    items = list(args)
    items.append(_KWMARK)
    for k in sorted(kwargs):
        items.append(k)
        items.append(kwargs[k])
    items.append(_KWMARK)
    items.extend(type(v) for v in args)
    for k in sorted(kwargs):
        items.append(type(kwargs[k]))
    return _HashedTuple(items)


def typedmethodkey(self: Any, *args: Any, **kwargs: Any) -> Tuple[Any, ...]:
    return typedkey(*args, **kwargs)