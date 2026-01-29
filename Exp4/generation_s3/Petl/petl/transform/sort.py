def _resolve_field_index(header, field):
    if isinstance(field, int):
        if field < 0 or field >= len(header):
            raise IndexError(field)
        return field
    try:
        return header.index(field)
    except ValueError:
        raise KeyError(field)


class SortView:
    def __init__(self, table, field):
        self.table = table
        self.field = field

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
        rows = [tuple(r) for r in it]
        rows.sort(key=lambda r: r[idx])
        for r in rows:
            yield r


def sort(table, field):
    """Sort data rows by a given field (name or index)."""
    return SortView(table, field)