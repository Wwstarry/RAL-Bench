from .. import _field_index, RowProxy


class SelectTable:
    """
    Lazily filter rows using a predicate taking a RowProxy.
    """
    def __init__(self, source, predicate):
        self._source = source
        self._predicate = predicate

    def __iter__(self):
        it = iter(self._source)
        header = next(it)
        yield tuple(header)
        name_to_index = {name: i for i, name in enumerate(header)}
        for row in it:
            rp = RowProxy(header, row, name_to_index=name_to_index)
            try:
                keep = self._predicate(rp)
            except Exception:
                # If predicate expects raw row, try passing tuple
                keep = self._predicate(row)
            if keep:
                yield tuple(row)


def select(table, predicate):
    """
    Filter rows by predicate(row).
    """
    return SelectTable(table, predicate)


class SelectCmpTable:
    """
    Lazy comparison-based selection on a single field.
    """
    def __init__(self, source, field, threshold, op):
        self._source = source
        self._field = field
        self._threshold = threshold
        self._op = op  # function: (value, threshold) -> bool

    def __iter__(self):
        it = iter(self._source)
        header = next(it)
        idx = _field_index(header, self._field)
        yield tuple(header)
        if idx is None:
            # Field not found: no rows match
            return
        for row in it:
            if idx < len(row):
                try:
                    if self._op(row[idx], self._threshold):
                        yield tuple(row)
                except Exception:
                    # If comparison fails due to type mismatch, skip row
                    continue


def selectge(table, field, threshold):
    """
    Select rows where field >= threshold.
    """
    return SelectCmpTable(table, field, threshold, op=lambda v, t: v >= t)


def selectgt(table, field, threshold):
    """
    Select rows where field > threshold.
    """
    return SelectCmpTable(table, field, threshold, op=lambda v, t: v > t)