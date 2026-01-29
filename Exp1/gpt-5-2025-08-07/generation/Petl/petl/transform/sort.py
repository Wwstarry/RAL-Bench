from .. import _field_index


class SortTable:
    """
    Materializes rows to sort by a single field; yields header then sorted rows.
    """
    def __init__(self, source, field):
        self._source = source
        self._field = field

    def __iter__(self):
        it = iter(self._source)
        header = next(it)
        idx = _field_index(header, self._field)
        yield tuple(header)
        # Materialize remaining rows for sorting
        rows = [tuple(row) for row in it]
        if idx is None:
            # No sort field; emit as-is
            for row in rows:
                yield row
            return

        def keyfunc(row):
            try:
                return row[idx]
            except Exception:
                return None

        rows.sort(key=keyfunc)
        for row in rows:
            yield row


def sort(table, field):
    """
    Sort rows by the specified field.
    """
    return SortTable(table, field)