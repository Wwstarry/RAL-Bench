def select(table, predicate):
    """
    Lazily yield rows for which predicate(row) is True.
    """
    return _SelectTable(table, predicate)

class _SelectTable:
    def __init__(self, source, predicate):
        self.source = source
        self.predicate = predicate

    def __iter__(self):
        it = iter(self.source)
        header = next(it)
        yield header

        for row in it:
            if self.predicate(row):
                yield row


def selectge(table, field, threshold):
    """
    Lazily yield rows where row[field] >= threshold.
    field can be a zero-based int index or a string matching a column name.
    """
    return _SelectComparisonTable(table, field, threshold, op='ge')


def selectgt(table, field, threshold):
    """
    Lazily yield rows where row[field] > threshold.
    field can be a zero-based int index or a string matching a column name.
    """
    return _SelectComparisonTable(table, field, threshold, op='gt')


def _field_index(header, field):
    if isinstance(field, int):
        return field
    else:
        return header.index(field)

class _SelectComparisonTable:
    def __init__(self, source, field, threshold, op):
        self.source = source
        self.field = field
        self.threshold = threshold
        self.op = op

    def __iter__(self):
        it = iter(self.source)
        header = next(it)
        yield header

        idx = _field_index(header, self.field)

        for row in it:
            val = row[idx]
            # Attempt numeric comparison if possible
            try:
                val = float(val)
                thr = float(self.threshold)
            except:
                # If conversion fails, skip or treat as string?
                # We'll treat them as strings for fallback
                val = str(val)
                thr = str(self.threshold)
            if self.op == 'ge':
                if val >= thr:
                    yield row
            elif self.op == 'gt':
                if val > thr:
                    yield row