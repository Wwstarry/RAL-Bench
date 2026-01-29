from .. import _field_index, RowProxy


class ConvertTable:
    """
    Lazy conversion of a single field via a function.
    """
    def __init__(self, source, field, func):
        self._source = source
        self._field = field
        self._func = func

    def __iter__(self):
        it = iter(self._source)
        header = next(it)
        idx = _field_index(header, self._field)
        yield tuple(header)
        if idx is None:
            # Field not found; pass-through
            for row in it:
                yield tuple(row)
            return
        for row in it:
            # Apply conversion to the specified field
            if idx < len(row):
                newval = self._func(row[idx])
                newrow = list(row)
                newrow[idx] = newval
                yield tuple(newrow)
            else:
                yield tuple(row)


def convert(table, field, func):
    """
    Convert values in a field using the provided function.
    """
    return ConvertTable(table, field, func)


class AddFieldTable:
    """
    Lazily add a computed field to each row, based on a function of the row.
    """
    def __init__(self, source, fieldname, func):
        self._source = source
        self._fieldname = fieldname
        self._func = func

    def __iter__(self):
        it = iter(self._source)
        header = next(it)
        out_header = list(header) + [self._fieldname]
        yield tuple(out_header)
        # Prebuild name->index mapping for RowProxy
        name_to_index = {name: i for i, name in enumerate(header)}
        for row in it:
            rp = RowProxy(header, row, name_to_index=name_to_index)
            newval = self._func(rp)
            newrow = list(row) + [newval]
            yield tuple(newrow)


def addfield(table, fieldname, func):
    """
    Add a new field computed by func(row).
    """
    return AddFieldTable(table, fieldname, func)