def sort(table, field):
    """
    Sort rows by a field (name or index).

    Note: sorting requires materializing data rows (not the whole pipeline).
    Header is preserved.
    """

    class _SortTable:
        def __init__(self, src, fld):
            self._src = src
            self._field = fld

        def __iter__(self):
            it = iter(self._src)
            header = next(it)
            header = tuple(header)

            if isinstance(self._field, int):
                idx = self._field
            else:
                try:
                    idx = header.index(self._field)
                except ValueError:
                    raise KeyError(self._field)

            rows = list(it)
            rows.sort(key=lambda r: r[idx])
            yield header
            for r in rows:
                yield tuple(r)

    return _SortTable(table, field)