import csv

def fromcsv(path):
    """
    Return a lazy table that reads from the CSV file at 'path'.
    The first row is treated as the header row.
    """
    return _CSVTable(path)

class _CSVTable:
    def __init__(self, path):
        self.path = path

    def __iter__(self):
        with open(self.path, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                yield row


def tocsv(table, path):
    """
    Write the rows of 'table' to a CSV file at 'path'.
    """
    with open(path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for row in table:
            writer.writerow(row)