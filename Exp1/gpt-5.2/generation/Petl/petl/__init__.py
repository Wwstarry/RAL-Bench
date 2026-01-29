"""
A lightweight, pure-Python subset of the petl API.

This package implements lazy table semantics:
- A "table" is any iterable of rows where the first row is the header.
- Transform functions return new lazy table wrappers.
"""

from .io.csv import fromcsv, tocsv
from .transform.conversions import convert
from .transform.selects import select, selectge, selectgt
from .transform.sort import sort
from .transform.joins import join


def fromdicts(records, header=None):
    """
    Construct a table from an iterable of dict-like records.

    Parameters
    ----------
    records : iterable of mappings
        Each record provides values by field name.
    header : list/tuple of str, optional
        If provided, defines output field order.
        If not provided, uses keys from the first record encountered.

    Returns
    -------
    table : iterable
        Yields header then rows.
    """

    def _iter():
        it = iter(records)
        first = None
        if header is None:
            for rec in it:
                first = rec
                break
            if first is None:
                # no records; yield empty header
                yield ()
                return
            hdr = list(first.keys())
            yield tuple(hdr)
            yield tuple(first.get(f) for f in hdr)
            for rec in it:
                yield tuple(rec.get(f) for f in hdr)
        else:
            hdr = list(header)
            yield tuple(hdr)
            for rec in it:
                yield tuple(rec.get(f) for f in hdr)

    return _iter()


def addfield(table, fieldname, func):
    """
    Add a new field computed per row.

    func may accept:
      - a row tuple/list
      - or a dict mapping fieldnames->values (if func expects dict, recommended).

    We pass a dict for convenience.
    """
    def _iter():
        it = iter(table)
        try:
            hdr = next(it)
        except StopIteration:
            return
        hdr = tuple(hdr)
        newhdr = hdr + (fieldname,)
        yield newhdr
        for row in it:
            row = tuple(row)
            rec = dict(zip(hdr, row))
            val = func(rec)
            yield row + (val,)
    return _iter()


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