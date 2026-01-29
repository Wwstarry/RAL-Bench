"""
Sorting helper.
"""

from .. import Table
from .conversions import _field_index


def sort(table, field):
    """
    Materialise *table*, sort rows by *field* (ascending), and expose the
    sorted view as a new table.

    Note: This operation necessarily loads all data into memory.
    """

    def _factory():
        rows = list(table)
        if not rows:
            return iter([])  # empty generator

        header = rows[0]
        idx = _field_index(header, field)
        data = sorted(rows[1:], key=lambda r: r[idx])
        yield header
        for r in data:
            yield r

    return Table(_factory)