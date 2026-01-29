def convert(table, field, func):
    """
    Convert a field/column by applying func to each value.

    field can be a field name (str) or a 0-based integer index.
    """
    def _iter():
        it = iter(table)
        try:
            hdr = next(it)
        except StopIteration:
            return
        hdr = tuple(hdr)
        yield hdr

        if isinstance(field, int):
            idx = field
        else:
            try:
                idx = hdr.index(field)
            except ValueError:
                raise KeyError(f"field not found: {field!r}")

        for row in it:
            row = list(row)
            row[idx] = func(row[idx])
            yield tuple(row)

    return _iter()