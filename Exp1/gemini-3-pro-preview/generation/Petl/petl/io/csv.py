import csv
import os

class CSVView:
    def __init__(self, path, encoding='utf-8', **kwargs):
        self.path = path
        self.encoding = encoding
        self.kwargs = kwargs

    def __iter__(self):
        with open(self.path, 'r', encoding=self.encoding, newline='') as f:
            reader = csv.reader(f, **self.kwargs)
            for row in reader:
                yield tuple(row)

def fromcsv(path, encoding='utf-8', **kwargs):
    """
    Extract a table from a CSV file.
    """
    return CSVView(path, encoding=encoding, **kwargs)

def tocsv(table, path, encoding='utf-8', **kwargs):
    """
    Load a table into a CSV file.
    """
    # Ensure directory exists
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(path, 'w', encoding=encoding, newline='') as f:
        writer = csv.writer(f, **kwargs)
        for row in table:
            writer.writerow(row)