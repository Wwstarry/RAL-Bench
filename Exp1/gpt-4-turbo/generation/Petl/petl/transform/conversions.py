class DictsTable:
    def __init__(self, records, header=None):
        self.records = records
        self.header = header

    def __iter__(self):
        records = self.records
        if self.header is not None:
            header = self.header
        else:
            try:
                first = next(iter(records))
            except StopIteration:
                header = []
            else:
                header = list(first.keys())
        yield tuple(header)
        for rec in records:
            yield tuple(rec.get(h, None) for h in header)

def fromdicts(records, header=None):
    """
    Construct a table from a sequence of dicts.
    """
    return DictsTable(records, header)

class ConvertTable:
    def __init__(self, table, field, func):
        self.table = table
        self.field = field
        self.func = func

    def __iter__(self):
        it = iter(self.table)
        header = next(it)
        try:
            idx = header.index(self.field)
        except ValueError:
            raise Exception(f"Field '{self.field}' not found in header")
        yield header
        for row in it:
            row = list(row)
            row[idx] = self.func(row[idx])
            yield tuple(row)

def convert(table, field, func):
    """
    Convert values in a column using a function.
    """
    return ConvertTable(table, field, func)

class AddFieldTable:
    def __init__(self, table, fieldname, func):
        self.table = table
        self.fieldname = fieldname
        self.func = func

    def __iter__(self):
        it = iter(self.table)
        header = next(it)
        new_header = tuple(list(header) + [self.fieldname])
        yield new_header
        for row in it:
            new_value = self.func(row)
            yield tuple(list(row) + [new_value])

def addfield(table, fieldname, func):
    """
    Add a new field to each row, computed by func(row).
    """
    return AddFieldTable(table, fieldname, func)