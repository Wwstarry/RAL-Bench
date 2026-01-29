import csv

class FromCSVTable:
    def __init__(self, path):
        self.path = path

    def __iter__(self):
        with open(self.path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                yield tuple(row)

def fromcsv(path):
    """
    Load a CSV file lazily as a table.
    """
    return FromCSVTable(path)

def tocsv(table, path):
    """
    Write a table to a CSV file.
    """
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        it = iter(table)
        try:
            header = next(it)
        except StopIteration:
            return
        writer.writerow(header)
        for row in it:
            writer.writerow(row)

class FromDictsTable:
    def __init__(self, records, header=None):
        self.records = records
        self.header = header
        self._header_determined = False
        self._header_cached = None

    def __iter__(self):
        if self.header is not None:
            header = tuple(self.header)
        else:
            # Determine header from first record keys lazily
            it = iter(self.records)
            try:
                first = next(it)
            except StopIteration:
                return
            header = tuple(first.keys())
            yield header
            yield tuple(first.get(h, None) for h in header)
            for rec in it:
                yield tuple(rec.get(h, None) for h in header)
            return
        yield header
        for rec in self.records:
            yield tuple(rec.get(h, None) for h in header)

def fromdicts(records, header=None):
    """
    Create a table from an iterable of dicts.
    """
    return FromDictsTable(records, header)