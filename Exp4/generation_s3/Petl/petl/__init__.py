"""
A lightweight, pure-Python subset of the petl API.

This package provides lazy table semantics: all transformation functions return
iterables that only evaluate their inputs when iterated.

Only a small set of functions are implemented to satisfy the accompanying test
suite; this is not the full petl project.
"""

from .io.csv import fromcsv, tocsv
from .transform.conversions import convert
from .transform.selects import select, selectge, selectgt, addfield
from .transform.sort import sort
from .transform.joins import join

__all__ = [
    "fromcsv",
    "tocsv",
    "fromdicts",
    "convert",
    "select",
    "selectge",
    "selectgt",
    "sort",
    "addfield",
    "join",
]


class DictsView:
    """Lazy table view over an iterable of dict-like records."""

    def __init__(self, records, header=None):
        self._records = records
        self._header = list(header) if header is not None else None

    def __iter__(self):
        it = iter(self._records)

        if self._header is None:
            # Derive header deterministically from first record encountered.
            try:
                first = next(it)
            except StopIteration:
                return
                yield  # pragma: no cover
            header = list(getattr(first, "keys")())
            yield tuple(header)
            yield tuple(first.get(f) for f in header)
            for rec in it:
                yield tuple(rec.get(f) for f in header)
        else:
            header = list(self._header)
            yield tuple(header)
            for rec in it:
                yield tuple(rec.get(f) for f in header)


def fromdicts(records, header=None):
    """Create a lazy table from an iterable of dict-like objects."""
    return DictsView(records, header=header)