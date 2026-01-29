def addfield(table, fieldname, func):
    def transformed():
        it = iter(table())
        header = next(it)
        yield header + [fieldname]
        for row in it:
            yield row + [func(row)]
    return transformed