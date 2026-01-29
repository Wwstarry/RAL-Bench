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


_kwd_mark = object()


def _make_key(args: Tuple[Any, ...], kwargs: dict, typed: bool) -> tuple:
    key = args
    if kwargs:
        # match cachetools/functools semantics: sorted by key
        items = tuple(sorted(kwargs.items()))
        key = key + (_kwd_mark,) + items
    if typed:
        key = key + tuple(type(v) for v in args)
        if kwargs:
            key = key + tuple(type(v) for _, v in sorted(kwargs.items()))
    return _HashedTuple(key)


def hashkey(*args, **kwargs):
    return _make_key(args, kwargs, typed=False)


def methodkey(self, *args, **kwargs):
    # ignore self/cls
    return _make_key(args, kwargs, typed=False)


def typedkey(*args, **kwargs):
    return _make_key(args, kwargs, typed=True)


def typedmethodkey(self, *args, **kwargs):
    return _make_key(args, kwargs, typed=True)