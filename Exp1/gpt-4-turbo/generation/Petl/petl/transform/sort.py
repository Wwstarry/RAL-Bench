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
            raise Exception(f"Field '{self.field}' not found in header")
        yield header
        # Materialize all rows for sorting
        rows = list(it)
        rows.sort(key=lambda row: row[idx])
        for row in rows:
            yield row

def sort(table, field):
    """
    Sort rows by field.
    """
    return SortTable(table, field)