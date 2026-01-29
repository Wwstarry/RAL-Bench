"""
CSV input/output operations.
"""

import csv

def fromcsv(path, encoding='utf-8'):
    """Read CSV file and return table."""
    def _read_csv():
        with open(path, 'r', encoding=encoding, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                yield row
    
    from ..core import Table
    return Table(_read_csv())


def tocsv(table, path, encoding='utf-8'):
    """Write table to CSV file."""
    with open(path, 'w', encoding=encoding, newline='') as f:
        writer = csv.writer(f)
        for row in table:
            writer.writerow(row)