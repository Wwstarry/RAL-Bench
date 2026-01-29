"""
Lightweight, pure-Python subset of the petl API used by the test suite.

This package implements lazy table semantics: transformations return iterable
wrappers which only evaluate when iterated.
"""

from .io.csv import fromcsv, tocsv
from .transform.conversions import convert
from .transform.selects import select, selectge, selectgt
from .transform.sort import sort
from .transform.joins import join


def fromdicts(records, header=None):
    """
    Create a table from an iterable of dict-like records.

    Parameters
    ----------
    records : iterable of mapping
        Each record provides values by field name.
    header : list/tuple of str, optional
        If provided, determines field order and included fields.
        If not provided, inferred from first record's keys (iteration order).

    Returns
    -------
    table : iterable
        First row is header tuple, subsequent rows are tuples of values.
    """

    class _FromDictsTable:
        def __init__(self, recs, hdr):
            self._records = recs
            self._header = hdr

        def __iter__(self):
            it = iter(self._records)
            if self._header is None:
                try:
                    first = next(it)
                except StopIteration:
                    # empty -> just header row (empty)
                    yield tuple()
                    return
                hdr = list(first.keys())
                yield tuple(hdr)
                yield tuple(first.get(f) for f in hdr)
                for rec in it:
                    yield tuple(rec.get(f) for f in hdr)
            else:
                hdr = list(self._header)
                yield tuple(hdr)
                for rec in it:
                    yield tuple(rec.get(f) for f in hdr)

    return _FromDictsTable(records, header)


def addfield(table, fieldname, func):
    """
    Add a new field computed from each row.

    func may accept either:
      - the entire row as a tuple (data row), or
      - a dict mapping field -> value (rowdict), depending on its signature.
    """

    class _AddFieldTable:
        def __init__(self, src, name, f):
            self._src = src
            self._name = name
            self._func = f

        def __iter__(self):
            it = iter(self._src)
            header = next(it)
            header = tuple(header)
            out_header = header + (self._name,)
            yield out_header

            # attempt to call func with dict first (more petl-like), fallback to tuple
            for row in it:
                row = tuple(row)
                rowdict = dict(zip(header, row))
                try:
                    val = self._func(rowdict)
                except TypeError:
                    val = self._func(row)
                yield row + (val,)

    return _AddFieldTable(table, fieldname, func)


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