def sort(table, field):
    def sorted_table():
        it = iter(table())
        header = next(it)
        idx = header.index(field)
        yield header
        yield from sorted(it, key=lambda row: row[idx])
    return sorted_table