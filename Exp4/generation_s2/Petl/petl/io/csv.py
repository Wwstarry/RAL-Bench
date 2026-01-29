import csv


class _CSVTable:
    def __init__(self, path, **csv_kwargs):
        self.path = path
        self.csv_kwargs = csv_kwargs

    def __iter__(self):
        # newline='' is required by csv module docs for correct handling
        with open(self.path, "r", newline="") as f:
            reader = csv.reader(f, **self.csv_kwargs)
            for row in reader:
                # keep as tuples for consistency
                yield tuple(row)


def fromcsv(path, **csv_kwargs):
    """
    Create a lazy table from a CSV file.

    Returns an iterable where the first row is the header.
    """
    return _CSVTable(path, **csv_kwargs)


def tocsv(table, path, **csv_kwargs):
    """
    Write a table to a CSV file.
    """
    with open(path, "w", newline="") as f:
        writer = csv.writer(f, **csv_kwargs)
        for row in table:
            writer.writerow(list(row))
    return path