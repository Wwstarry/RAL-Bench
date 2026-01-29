import csv


def fromcsv(path, encoding="utf-8", newline=""):
    """
    Lazily read a CSV file, yielding rows as tuples.

    The first yielded row is the header (as found in the file).
    """
    def _iter():
        with open(path, "r", encoding=encoding, newline=newline) as f:
            reader = csv.reader(f)
            for row in reader:
                yield tuple(row)
    return _iter()


def tocsv(table, path, encoding="utf-8", newline=""):
    """
    Write a table to CSV.

    Materialization is avoided beyond streaming iteration.
    """
    with open(path, "w", encoding=encoding, newline=newline) as f:
        writer = csv.writer(f)
        for row in table:
            writer.writerow(list(row))
    return path