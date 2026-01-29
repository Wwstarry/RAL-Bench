"""
Type and value conversion helpers.
"""

from .. import Table


def _field_index(header, field):
    """
    Resolve *field* (name or integer index) to a numeric position within *header*.
    """
    if isinstance(field, int):
        return field
    try:
        return header.index(field)
    except ValueError:  # pragma: no cover
        raise KeyError(f"field {field!r} not in header")


def convert(table, field, func):
    """
    Return a *new* table in which *field* values are replaced by
    ``func(value)``.

    The operation is performed lazily row by row at iteration-time.
    """

    def _factory():
        it = iter(table)
        header = next(it)
        idx = _field_index(header, field)
        yield header
        for row in it:
            lst = list(row)
            lst[idx] = func(lst[idx])
            yield tuple(lst)

    return Table(_factory)


def addfield(table, fieldname, func):
    """
    Append a *new* field named *fieldname* computed via ``func(row)``.
    """

    def _factory():
        it = iter(table)
        header = next(it)
        new_header = tuple(list(header) + [fieldname])
        yield new_header
        for row in it:
            from .. import RowProxy  # local import to avoid cycles
            proxy = RowProxy(header, row)
            new_value = func(proxy)
            yield tuple(list(row) + [new_value])

    return Table(_factory)