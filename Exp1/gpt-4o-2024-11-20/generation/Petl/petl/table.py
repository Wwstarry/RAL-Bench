def fromdicts(records, header=None):
    def table():
        if header is None:
            if not records:
                yield []
            else:
                yield list(records[0].keys())
        else:
            yield header
        for record in records:
            yield [record.get(h, None) for h in header]
    return table