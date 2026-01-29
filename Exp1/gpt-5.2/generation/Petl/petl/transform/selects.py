def select(table, predicate):
    """
    Filter rows by predicate.

    predicate is called with a dict mapping field names to values.
    Header is always passed through.
    """
    def _iter():
        it = iter(table)
        try:
            hdr = next(it)
        except StopIteration:
            return
        hdr = tuple(hdr)
        yield hdr
        for row in it:
            row = tuple(row)
            rec = dict(zip(hdr, row))
            if predicate(rec):
                yield row
    return _iter()


def _resolve_index(hdr, field):
    if isinstance(field, int):
        return field
    try:
        return hdr.index(field)
    except ValueError:
        raise KeyError(f"field not found: {field!r}")


def selectge(table, field, threshold):
    """Select rows where row[field] >= threshold."""
    def _iter():
        it = iter(table)
        try:
            hdr = next(it)
        except StopIteration:
            return
        hdr = tuple(hdr)
        yield hdr
        idx = _resolve_index(hdr, field)
        for row in it:
            row = tuple(row)
            if row[idx] >= threshold:
                yield row
    return _iter()


def selectgt(table, field, threshold):
    """Select rows where row[field] > threshold."""
    def _iter():
        it = iter(table)
        try:
            hdr = next(it)
        except StopIteration:
            return
        hdr = tuple(hdr)
        yield hdr
        idx = _resolve_index(hdr, field)
        for row in it:
            row = tuple(row)
            if row[idx] > threshold:
                yield row
    return _iter()