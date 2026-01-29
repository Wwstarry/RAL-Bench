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
    Select rows where predicate(row) is True.
    """
    return SelectTable(table, predicate)

class SelectGE:
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
            # field not found, yield all rows
            yield header
            yield from it
            return
        yield header
        for row in it:
            try:
                if row[idx] >= self.threshold:
                    yield row
            except Exception:
                # On comparison error, skip row
                pass

def selectge(table, field, threshold):
    """
    Select rows where field >= threshold.
    """
    return SelectGE(table, field, threshold)

class SelectGT:
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
            yield header
            yield from it
            return
        yield header
        for row in it:
            try:
                if row[idx] > self.threshold:
                    yield row
            except Exception:
                pass

def selectgt(table, field, threshold):
    """
    Select rows where field > threshold.
    """
    return SelectGT(table, field, threshold)

class AddFieldTable:
    def __init__(self, table, fieldname, func):
        self.table = table
        self.fieldname = fieldname
        self.func = func

    def __iter__(self):
        it = iter(self.table)
        header = next(it)
        new_header = tuple(header) + (self.fieldname,)
        yield new_header
        for row in it:
            try:
                val = self.func(row)
            except Exception:
                val = None
            yield tuple(row) + (val,)

def addfield(table, fieldname, func):
    """
    Add a new field to each row, value computed by func(row).
    """
    return AddFieldTable(table, fieldname, func)