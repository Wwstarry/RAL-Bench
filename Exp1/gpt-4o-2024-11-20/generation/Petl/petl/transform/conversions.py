def convert(table, field, func):
    def transformed():
        it = iter(table())
        header = next(it)
        idx = header.index(field)
        yield header
        for row in it:
            new_row = list(row)
            new_row[idx] = func(row[idx])
            yield new_row
    return transformed