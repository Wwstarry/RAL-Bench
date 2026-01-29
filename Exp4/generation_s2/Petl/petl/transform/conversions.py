def convert(table, field, func):
    """
    Convert values in a field using func.

    field may be a field name (str) or column index (int).
    func is applied to the existing value; exceptions are allowed to propagate.
    """

    class _ConvertTable:
        def __init__(self, src, fld, f):
            self._src = src
            self._field = fld
            self._func = f

        def __iter__(self):
            it = iter(self._src)
            header = next(it)
            header = tuple(header)
            yield header

            if isinstance(self._field, int):
                idx = self._field
            else:
                try:
                    idx = header.index(self._field)
                except ValueError:
                    raise KeyError(self._field)

            for row in it:
                row = list(row)
                row[idx] = self._func(row[idx])
                yield tuple(row)

    return _ConvertTable(table, field, func)