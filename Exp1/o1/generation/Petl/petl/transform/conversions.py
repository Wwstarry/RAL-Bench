def _field_index(header, field):
    """
    Resolve a field spec (int or str) to an integer index.
    """
    if isinstance(field, int):
        return field
    else:
        # Field is a string, find by name
        return header.index(field)

def convert(table, field, func):
    """
    Lazily convert the values of a specified field using 'func'.
    Field can be a zero-based int index or a string matching
    a column in the header.
    """
    return _ConvertTable(table, field, func)

class _ConvertTable:
    def __init__(self, source, field, func):
        self.source = source
        self.field = field
        self.func = func

    def __iter__(self):
        it = iter(self.source)
        header = next(it)
        yield header

        # Resolve field index
        fidx = _field_index(header, self.field)

        for row in it:
            row = list(row)  # make a copy to modify
            try:
                row[fidx] = self.func(row[fidx])
            except Exception:
                # If there's an error converting, let's just store None
                row[fidx] = None
            yield row


def addfield(table, fieldname, func):
    """
    Lazily add a new column 'fieldname' computed by `func(row)`.
    """
    return _AddFieldTable(table, fieldname, func)

class _AddFieldTable:
    def __init__(self, source, fieldname, func):
        self.source = source
        self.fieldname = fieldname
        self.func = func

    def __iter__(self):
        it = iter(self.source)
        old_header = next(it)
        new_header = list(old_header) + [self.fieldname]
        yield new_header

        for row in it:
            row = list(row)
            val = self.func(row)
            row.append(val)
            yield row