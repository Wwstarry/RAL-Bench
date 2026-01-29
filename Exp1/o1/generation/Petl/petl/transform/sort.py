def sort(table, field=None):
    """
    Return a lazily-sorted table. All data is read into memory, then sorted,
    then rows are yielded in sorted order. If 'field' is None, the entire row
    is used for sorting. If 'field' is specified (int or str), sorting is
    based on that column.
    """
    return _SortTable(table, field)

class _SortTable:
    def __init__(self, source, field):
        self.source = source
        self.field = field

    def __iter__(self):
        it = iter(self.source)
        header = next(it)
        yield header

        data = list(it)

        if self.field is None:
            data.sort()
        else:
            # find field index
            if isinstance(self.field, int):
                fidx = self.field
            else:
                fidx = header.index(self.field)

            data.sort(key=lambda row: row[fidx])

        for row in data:
            yield row