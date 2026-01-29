import csv

class CsvTable:
    def __init__(self, path):
        self.path = path

    def __iter__(self):
        with open(self.path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                yield tuple(row)

def fromcsv(path):
    """
    Read a CSV file and return a lazy table.
    """
    return CsvTable(path)

def tocsv(table, path):
    """
    Write a table to a CSV file.
    """
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for row in table:
            writer.writerow(row)