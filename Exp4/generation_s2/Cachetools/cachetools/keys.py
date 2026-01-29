from __future__ import annotations

from typing import Any, Tuple


def _kwmark():
    return object()


_KWMARK = _kwmark()


def hashkey(*args: Any, **kwargs: Any) -> Tuple[Any, ...]:
    """
    Return a hashable key for the given arguments.

    Matches the common cachetools behavior: a tuple of positional args, and if
    kwargs are present, a unique marker followed by sorted (key, value) pairs.
    """
    if not kwargs:
        return args
    items = tuple(sorted(kwargs.items()))
    return args + (_KWMARK,) + items


def typedkey(*args: Any, **kwargs: Any) -> Tuple[Any, ...]:
    """
    Like hashkey, but also include argument types (positional and keyword values).
    """
    key = hashkey(*args, **kwargs)
    types = tuple(type(v) for v in args)
    if kwargs:
        kwtypes = tuple(type(v) for _, v in sorted(kwargs.items()))
        types = types + kwtypes
    return key + (_KWMARK,) + types


def methodkey(self: Any, *args: Any, **kwargs: Any) -> Tuple[Any, ...]:
    """Key function for cached methods; ignores 'self'."""
    return hashkey(*args, **kwargs)


def typedmethodkey(self: Any, *args: Any, **kwargs: Any) -> Tuple[Any, ...]:
    """Typed variant for cached methods; ignores 'self'."""
    return typedkey(*args, **kwargs)