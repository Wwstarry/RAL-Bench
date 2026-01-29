class SortView:
    def __init__(self, source, field, reverse=False):
        self.source = source
        self.field = field
        self.reverse = reverse

    def __iter__(self):
        it = iter(self.source)
        try:
            header = next(it)
        except StopIteration:
            return

        yield tuple(header)

        # Identify sort key index
        # field can be a single field name or a list of names
        if isinstance(self.field, (list, tuple)):
            indices = [header.index(f) for f in self.field]
            key_func = lambda r: tuple(r[i] for i in indices)
        else:
            idx = header.index(self.field)
            key_func = lambda r: r[idx]

        # Materialize data rows to sort
        rows = list(it)
        rows.sort(key=key_func, reverse=self.reverse)

        for row in rows:
            yield tuple(row)

def sort(table, field, reverse=False):
    """
    Sort the table by a field or list of fields.
    """
    return SortView(table, field, reverse)