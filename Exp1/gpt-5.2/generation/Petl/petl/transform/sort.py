def sort(table, field):
    """
    Sort table by field (name or index).

    Note: sorting necessarily materializes data rows (but keeps header).
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

        rows = list(it)
        rows.sort(key=lambda r: r[idx])
        for r in rows:
            yield tuple(r)

    return _iter()