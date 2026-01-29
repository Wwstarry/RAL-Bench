class SortTable:
    def __init__(self, table, field):
        self.table = table
        self.field = field

    def __iter__(self):
        it = iter(self.table)
        header = next(it)
        try:
            idx = header.index(self.field)
        except ValueError:
            # field not found, yield unsorted
            yield header
            yield from it
            return
        rows = list(it)
        try:
            rows.sort(key=lambda r: r[idx])
        except Exception:
            # fallback: sort by string representation
            rows.sort(key=lambda r: str(r[idx]))
        yield header
        yield from rows

def sort(table, field):
    """
    Sort table rows by field ascending.
    """
    return SortTable(table, field)