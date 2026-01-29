import csv


class CsvTable:
    """
    Lazy CSV reader that yields header and rows when iterated.
    """
    def __init__(self, path, encoding="utf-8", newline=""):
        self._path = path
        self._encoding = encoding
        self._newline = newline

    def __iter__(self):
        with open(self._path, "r", encoding=self._encoding, newline=self._newline) as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                return
            yield tuple(header)
            for row in reader:
                yield tuple(row)


def fromcsv(path):
    """
    Read a CSV file lazily, producing a table where the first row is the header.
    """
    return CsvTable(path)


def tocsv(table, path, encoding="utf-8", newline=""):
    """
    Write a table to CSV. Consumes the table lazily during write.
    """
    with open(path, "w", encoding=encoding, newline=newline) as f:
        writer = csv.writer(f)
        for row in table:
            writer.writerow(list(row))