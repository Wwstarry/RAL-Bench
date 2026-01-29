def select(table, predicate):
    def filtered():
        it = iter(table())
        yield next(it)  # header
        for row in it:
            if predicate(row):
                yield row
    return filtered

def selectge(table, field, threshold):
    def filtered():
        it = iter(table())
        header = next(it)
        idx = header.index(field)
        yield header
        for row in it:
            if row[idx] >= threshold:
                yield row
    return filtered

def selectgt(table, field, threshold):
    def filtered():
        it = iter(table())
        header = next(it)
        idx = header.index(field)
        yield header
        for row in it:
            if row[idx] > threshold:
                yield row
    return filtered