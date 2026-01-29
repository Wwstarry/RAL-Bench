# Lightweight ETL library with lazy table semantics
# Top-level petl API

from .io.csv import fromcsv, tocsv
from .transform.conversions import convert, addfield
from .transform.selects import select, selectge, selectgt
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


def _field_index(header, field):
    """
    Resolve a field spec (name or int index) to an index in the header.
    Returns None if not found.
    """
    if isinstance(field, int):
        return field
    if isinstance(field, str):
        try:
            return list(header).index(field)
        except ValueError:
            return None
    return None


class RowProxy:
    """
    Lightweight proxy for a row providing access by index or field name.
    """
    __slots__ = ("_row", "_name_to_index")

    def __init__(self, header, row, name_to_index=None):
        self._row = row
        if name_to_index is None:
            # Build mapping once per header
            self._name_to_index = {name: i for i, name in enumerate(header)}
        else:
            self._name_to_index = name_to_index

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._row[key]
        elif isinstance(key, str):
            idx = self._name_to_index.get(key)
            if idx is None:
                raise KeyError(f"Field {key!r} not found")
            return self._row[idx]
        else:
            raise TypeError("RowProxy indices must be int or str")

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


class DictsTable:
    """
    Table wrapper for in-memory records provided as dictionaries.
    Lazily iterates over the records and emits header + rows.
    """
    def __init__(self, records, header=None):
        self._records = records
        self._header = header

    def __iter__(self):
        # Try to determine header
        header = self._header
        if header is None:
            # Attempt to infer header from first record if available
            # If records is a sequence, we can access first element without consuming
            try:
                # Prefer sequence protocol
                first = self._records[0]  # may raise TypeError if not sequence
                header = list(first.keys())
            except Exception:
                # Fallback: consume first item from an iterator and rebuild iterator by tee
                # Note: if records is a one-shot iterator, subsequent iterations may not work
                # Tests typically pass list/tuple; for generators this is best-effort.
                import itertools
                it1, it2 = itertools.tee(iter(self._records), 2)
                try:
                    first = next(it1)
                except StopIteration:
                    # Empty input
                    yield tuple()
                    return
                header = list(first.keys())
                # Rebuild a new iterable combining first + rest
                def rows_iter():
                    yield first
                    for rec in it1:
                        yield rec
                # Set _records to re-iterable sequence
                self._records = list(it2)
                # Continue using rebuilt sequence below

        # Emit rows
        yield tuple(header)
        # Iterate records lazily
        for rec in self._records:
            # Ensure keys present; missing values -> None
            row = tuple(rec.get(f) for f in header)
            yield row


def fromdicts(records, header=None):
    """
    Construct a table from an iterable of dictionaries.
    The header can be provided explicitly; otherwise inferred from the first record.
    """
    return DictsTable(records, header=header)