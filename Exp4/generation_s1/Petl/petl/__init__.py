"""
A lightweight, pure-Python subset of the petl API.

This package implements a small lazy ETL (Extract-Transform-Load) toolkit with
table semantics compatible with the core behaviors exercised by the tests.

Table protocol:
- A table is any iterable yielding rows.
- The first row is a header (sequence of field names).
- Subsequent rows are data rows (sequences).
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, Union

Field = Union[int, str]
Row = Tuple[Any, ...]
Header = Tuple[Any, ...]


def _as_tuple(row: Sequence[Any]) -> Tuple[Any, ...]:
    if isinstance(row, tuple):
        return row
    return tuple(row)


def _as_field_index(header: Sequence[Any], field: Field) -> int:
    if isinstance(field, int):
        if field < 0 or field >= len(header):
            raise IndexError(field)
        return field
    else:
        try:
            return list(header).index(field)
        except ValueError as e:
            raise KeyError(field) from e


def _iter_table(table: Iterable[Sequence[Any]]) -> Iterator[Tuple[Any, ...]]:
    for row in table:
        yield _as_tuple(row)


def fromdicts(records: Iterable[Dict[str, Any]], header: Optional[Sequence[str]] = None):
    """
    Create a table from an iterable of dictionaries.

    If header is provided, fields are taken in that order. Missing keys yield None.
    If header is None, header is inferred from the first record's keys (in insertion order).
    The records are materialized into a list to ensure re-iterability.
    """
    recs = list(records)

    if header is None:
        if recs:
            header = list(recs[0].keys())
        else:
            header = []

    header_t = tuple(header)

    class DictsView:
        def __iter__(self) -> Iterator[Row]:
            yield header_t
            for rec in recs:
                yield tuple(rec.get(f, None) for f in header_t)

    return DictsView()


def addfield(table: Iterable[Sequence[Any]], fieldname: str, func: Callable, index: Optional[int] = None):
    """
    Add a derived field computed per row.

    func is called with (row) first; if that fails due to TypeError, it is called
    with a dict mapping field->value.
    """

    class AddFieldView:
        def __iter__(self) -> Iterator[Row]:
            it = _iter_table(table)
            header = next(it)
            if index is None:
                new_header = header + (fieldname,)
                insert_at = len(header)
            else:
                insert_at = index
                if insert_at < 0:
                    insert_at = max(0, len(header) + 1 + insert_at)
                if insert_at > len(header):
                    insert_at = len(header)
                new_header = header[:insert_at] + (fieldname,) + header[insert_at:]
            yield new_header

            # Precompute for dict fallback
            hdr_list = list(header)

            for row in it:
                try:
                    v = func(row)
                except TypeError:
                    v = func(dict(zip(hdr_list, row)))
                out = row[:insert_at] + (v,) + row[insert_at:]
                yield out

    return AddFieldView()


# Re-export public API from submodules
from .io.csv import fromcsv, tocsv  # noqa: E402
from .transform.conversions import convert  # noqa: E402
from .transform.selects import select, selectge, selectgt  # noqa: E402
from .transform.sort import sort  # noqa: E402
from .transform.joins import join  # noqa: E402

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