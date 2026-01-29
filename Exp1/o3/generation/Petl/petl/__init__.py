"""
A lightweight, pure-Python subset of the Petl ETL library.

Only the subset of functionality required by the test-suite is implemented.
The public surface re-exports the user-facing helpers that create and
manipulate lazy *table* objects.

Usage example:

    import petl

    people = petl.fromcsv('people.csv')
    adults = petl.selectge(people, 'age', 18)
    petl.tocsv(adults, 'adults.csv')
"""

from functools import partial

# ----------------------------------------------------------------------
# internal utilities
# ----------------------------------------------------------------------


class RowProxy:
    """
    A very small, read-only adapter around a data row that allows access by
    integer position **or** field name.

    The proxy presents a tuple-like interface so existing tuple logic keeps
    working, but additionally supports ``row['field']`` look-ups which the
    reference Petl library offers and which the public tests rely on.
    """

    __slots__ = ("_values", "_header", "_mapping")

    def __init__(self, header, values):
        self._values = tuple(values)
        self._header = tuple(header)
        # lazily build a mapping dict on first string lookup
        self._mapping = None

    # ------------------------------------------------------------------
    # tuple-like features
    # ------------------------------------------------------------------

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def __repr__(self):
        preview = ", ".join(map(repr, self._values[:5]))
        if len(self._values) > 5:
            preview += ", …"
        return f"<RowProxy ({preview})>"

    # ------------------------------------------------------------------
    # element access
    # ------------------------------------------------------------------

    def __getitem__(self, item):
        if isinstance(item, str):
            # build the mapping only when necessary
            if self._mapping is None:
                self._mapping = {name: pos for pos, name in enumerate(self._header)}
            try:
                item = self._mapping[item]
            except KeyError:
                raise KeyError(f"unknown field name {item!r}") from None
        return self._values[item]


class Table:
    """
    Light-weight wrapper around a *factory* callback returning a fresh
    iterator over the table rows each time the table is iterated.

    The first row must contain the header.
    """

    __slots__ = ("_it_factory",)

    def __init__(self, iterator_factory):
        self._it_factory = iterator_factory

    # ------------------------------------------------------------------
    # protocol
    # ------------------------------------------------------------------

    def __iter__(self):
        return self._it_factory()

    # convenient helper for the tests
    def tolist(self):
        return list(self)

    # friendly representation in a REPL
    def __repr__(self):
        try:
            head = list(self)[:5]
            text = ", ".join(map(repr, head))
            return f"<Table [{text}{', …' if len(head) == 5 else ''}]>"
        except Exception:
            return "<Table (unavailable)>"


# ----------------------------------------------------------------------
# IO helpers
# ----------------------------------------------------------------------

from .io.csv import fromcsv, tocsv  # noqa: E402

# ----------------------------------------------------------------------
# transformation helpers
# ----------------------------------------------------------------------

from .transform.conversions import convert, addfield  # noqa: E402
from .transform.selects import select, selectge, selectgt  # noqa: E402
from .transform.sort import sort  # noqa: E402
from .transform.joins import join  # noqa: E402

# ----------------------------------------------------------------------
# in-memory construction helpers
# ----------------------------------------------------------------------


def fromdicts(records, header=None):
    """
    Build a table from an *iterable* of dictionaries.

    Parameters
    ----------
    records : iterable of dict
        Source items.
    header : sequence of str, optional
        Explicit header order.  If *None*, the keys of the **first** record
        define the header order.  Missing values are rendered as ``None``.
    """

    def _factory():
        rec_iter = iter(records)
        try:
            first = next(rec_iter)
        except StopIteration:
            # empty source – yield header if specified or nothing at all
            if header is not None:
                yield tuple(header)
            return

        hdr = tuple(header) if header is not None else tuple(first.keys())
        yield hdr

        # helper to materialise a row in the correct order
        def _values(rec):
            return tuple(rec.get(col) for col in hdr)

        # first row (already fetched)
        yield _values(first)
        # remaining rows
        for rec in rec_iter:
            yield _values(rec)

    return Table(_factory)


# public names
__all__ = [
    # construction
    "fromcsv",
    "tocsv",
    "fromdicts",
    # transforms
    "convert",
    "addfield",
    "select",
    "selectge",
    "selectgt",
    "sort",
    "join",
]