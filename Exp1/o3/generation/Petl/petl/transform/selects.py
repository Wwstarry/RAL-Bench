"""
Row filtering helpers.
"""

from .. import Table, RowProxy
from .conversions import _field_index


def select(table, predicate):
    """
    Keep only rows for which *predicate(row_proxy)* evaluates to truthy.
    """

    def _factory():
        it = iter(table)
        header = next(it)
        yield header
        for row in it:
            proxy = RowProxy(header, row)
            if predicate(proxy):
                yield row

    return Table(_factory)


# ----------------------------------------------------------------------
# comparison-based selectors
# ----------------------------------------------------------------------


def _make_cmp_selector(op_name):
    import operator as _op_map

    op_func = getattr(_op_map, op_name)

    def _selector(table, field, threshold):
        def _factory():
            it = iter(table)
            header = next(it)
            idx = _field_index(header, field)
            yield header
            for row in it:
                if op_func(row[idx], threshold):
                    yield row

        return Table(_factory)

    _selector.__name__ = f"select{op_name}"
    return _selector


# Generate selectge and selectgt
selectge = _make_cmp_selector("ge")
selectgt = _make_cmp_selector("gt")

__all__ = ["select", "selectge", "selectgt"]