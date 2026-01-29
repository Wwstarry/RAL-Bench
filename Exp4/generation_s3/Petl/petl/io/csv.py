import csv


class CSVView:
    """Lazy table reading from a CSV file; re-iterable by reopening the file."""

    def __init__(self, path, reader_kwargs=None):
        self.path = path
        self.reader_kwargs = dict(reader_kwargs or {})

    def __iter__(self):
        # Lazily open/read on iteration.
        with open(self.path, "r", newline="") as f:
            rdr = csv.reader(f, **self.reader_kwargs)
            for row in rdr:
                # Return tuples for immutability and predictable behavior.
                yield tuple(row)


def fromcsv(path, **kwargs):
    """
    Read a CSV file lazily and return a table (iterable of rows).
    kwargs are forwarded to csv.reader.
    """
    return CSVView(path, reader_kwargs=kwargs)


def tocsv(table, path, **kwargs):
    """
    Write a table to a CSV file.
    kwargs are forwarded to csv.writer.
    """
    with open(path, "w", newline="") as f:
        w = csv.writer(f, **kwargs)
        for row in table:
            w.writerow(list(row) if not isinstance(row, (list, tuple)) else row)