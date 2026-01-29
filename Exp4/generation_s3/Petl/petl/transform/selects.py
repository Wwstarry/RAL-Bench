def _resolve_field_index(header, field):
    if isinstance(field, int):
        if field < 0 or field >= len(header):
            raise IndexError(field)
        return field
    try:
        return header.index(field)
    except ValueError:
        raise KeyError(field)


class SelectView:
    def __init__(self, table, predicate):
        self.table = table
        self.predicate = predicate

    def __iter__(self):
        it = iter(self.table)
        try:
            header = next(it)
        except StopIteration:
            return
            yield  # pragma: no cover

        yield tuple(header)

        for row in it:
            row_t = tuple(row)
            if self.predicate(row_t):
                yield row_t


def select(table, predicate):
    """Filter rows using predicate(row) applied to data rows."""
    return SelectView(table, predicate)


class SelectCompareView:
    def __init__(self, table, field, threshold, op):
        self.table = table
        self.field = field
        self.threshold = threshold
        self.op = op

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
        thr = self.threshold
        op = self.op

        for row in it:
            row_t = tuple(row)
            if op(row_t[idx], thr):
                yield row_t


def selectge(table, field, threshold):
    """Keep rows where row[field] >= threshold."""
    return SelectCompareView(table, field, threshold, op=lambda a, b: a >= b)


def selectgt(table, field, threshold):
    """Keep rows where row[field] > threshold."""
    return SelectCompareView(table, field, threshold, op=lambda a, b: a > b)


class AddFieldView:
    def __init__(self, table, fieldname, func):
        self.table = table
        self.fieldname = fieldname
        self.func = func

    def __iter__(self):
        it = iter(self.table)
        try:
            header = next(it)
        except StopIteration:
            return
            yield  # pragma: no cover

        header = list(header)
        header.append(self.fieldname)
        yield tuple(header)

        for row in it:
            row_t = tuple(row)
            newval = self.func(row_t)
            yield tuple(list(row_t) + [newval])


def addfield(table, fieldname, func):
    """Append a new field computed as func(row) for each data row."""
    return AddFieldView(table, fieldname, func)