# petl/transform/selects.py

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


def select(table, predicate):
    """
    Filter rows based on a predicate function.
    The predicate receives a row proxy object allowing access to values by field name.
    """
    it = iter(table)
    try:
        header = tuple(next(it))
        yield header
    except StopIteration:
        return

    proxy = RowProxy(header)
    for row in it:
        if predicate(proxy.set_row(row)):
            yield row

def selectge(table, field, threshold):
    """
    Select rows where the value of a field is greater than or equal to a threshold.
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
        if row[field_index] >= threshold:
            yield row

def selectgt(table, field, threshold):
    """
    Select rows where the value of a field is greater than a threshold.
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
        if row[field_index] > threshold:
            yield row