class SelectView:
    def __init__(self, source, predicate):
        self.source = source
        self.predicate = predicate

    def __iter__(self):
        it = iter(self.source)
        try:
            header = next(it)
        except StopIteration:
            return
        
        yield tuple(header)
        
        for row in it:
            # To support predicate(record), we map to dict
            rec = dict(zip(header, row))
            if self.predicate(rec):
                yield tuple(row)

def select(table, predicate):
    """
    Select rows where predicate(row) is True.
    """
    return SelectView(table, predicate)

class SelectCompareView:
    def __init__(self, source, field, threshold, op):
        self.source = source
        self.field = field
        self.threshold = threshold
        self.op = op

    def __iter__(self):
        it = iter(self.source)
        try:
            header = next(it)
        except StopIteration:
            return

        yield tuple(header)

        try:
            idx = header.index(self.field)
        except ValueError:
            raise ValueError(f"Field {self.field} not in header")

        for row in it:
            if idx < len(row):
                val = row[idx]
                # Handle type conversion implicitly or assume data is clean
                # Petl usually handles loose typing, but here we assume comparable types
                try:
                    if self.op(val, self.threshold):
                        yield tuple(row)
                except TypeError:
                    # Fallback for mixed types (e.g. str vs int comparison issues)
                    # Skip or fail? Petl usually tries hard.
                    pass

def selectge(table, field, threshold):
    """
    Select rows where field >= threshold.
    """
    return SelectCompareView(table, field, threshold, lambda a, b: a >= b)

def selectgt(table, field, threshold):
    """
    Select rows where field > threshold.
    """
    return SelectCompareView(table, field, threshold, lambda a, b: a > b)