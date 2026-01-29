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
            # field not found, yield unchanged
            yield header
            yield from it
            return
        yield header
        for row in it:
            row = list(row)
            try:
                row[idx] = self.func(row[idx])
            except Exception:
                # On conversion error, keep original value
                pass
            yield tuple(row)

def convert(table, field, func):
    """
    Convert values in a column using func.
    """
    return ConvertTable(table, field, func)