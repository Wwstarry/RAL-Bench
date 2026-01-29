def _resolve_field_index(header, field):
    if isinstance(field, int):
        if field < 0 or field >= len(header):
            raise IndexError(field)
        return field
    try:
        return header.index(field)
    except ValueError:
        raise KeyError(field)


class ConvertView:
    def __init__(self, table, field, func):
        self.table = table
        self.field = field
        self.func = func

    def __iter__(self):
        it = iter(self.table)
        try:
            header = next(it)
        except StopIteration:
            return
            yield  # pragma: no cover

        header = tuple(header)
        yield header

        idx = _resolve_field_index(header, self.field)

        for row in it:
            row = list(row)
            row[idx] = self.func(row[idx])
            yield tuple(row)


def convert(table, field, func):
    """Apply func(value) to every data cell in the specified field."""
    return ConvertView(table, field, func)