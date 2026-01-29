# petl/transform/conversions.py

class RowProxy:
    """A helper to provide dict-like access to a row tuple using a cached header mapping."""
    def __init__(self, header):
        self._mapping = {field: i for i, field in enumerate(header)}
        self._row = None

    def set_row(self, row):
        self._row = row
        return self

    def __getitem__(self, key):
        return self._row[self._mapping[key]]

def convert(table, field, func):
    """
    Transform values in a single column.
    """
    it = iter(table)
    try:
        header = tuple(next(it))
        yield header
    except StopIteration:
        return

    try:
        field_index = header.index(field)
    except ValueError:
        raise ValueError(f"Field not found: {repr(field)}")

    for row in it:
        new_row = list(row)
        # Let conversion errors propagate
        new_row[field_index] = func(new_row[field_index])
        yield tuple(new_row)


def addfield(table, fieldname, func):
    """
    Add a new field to the table.
    """
    it = iter(table)
    try:
        header = tuple(next(it))
        yield header + (fieldname,)
    except StopIteration:
        return

    proxy = RowProxy(header)
    for row in it:
        new_value = func(proxy.set_row(row))
        yield row + (new_value,)