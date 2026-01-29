class SelectTable:
    def __init__(self, table, predicate):
        self.table = table
        self.predicate = predicate

    def __iter__(self):
        it = iter(self.table)
        header = next(it)
        yield header
        for row in it:
            if self.predicate(row):
                yield row

def select(table, predicate):
    """
    Filter rows by predicate(row).
    """
    return SelectTable(table, predicate)

class SelectGeTable:
    def __init__(self, table, field, threshold):
        self.table = table
        self.field = field
        self.threshold = threshold

    def __iter__(self):
        it = iter(self.table)
        header = next(it)
        try:
            idx = header.index(self.field)
        except ValueError:
            raise Exception(f"Field '{self.field}' not found in header")
        yield header
        for row in it:
            if row[idx] >= self.threshold:
                yield row

def selectge(table, field, threshold):
    """
    Filter rows where field >= threshold.
    """
    return SelectGeTable(table, field, threshold)

class SelectGtTable:
    def __init__(self, table, field, threshold):
        self.table = table
        self.field = field
        self.threshold = threshold

    def __iter__(self):
        it = iter(self.table)
        header = next(it)
        try:
            idx = header.index(self.field)
        except ValueError:
            raise Exception(f"Field '{self.field}' not found in header")
        yield header
        for row in it:
            if row[idx] > self.threshold:
                yield row

def selectgt(table, field, threshold):
    """
    Filter rows where field > threshold.
    """
    return SelectGtTable(table, field, threshold)