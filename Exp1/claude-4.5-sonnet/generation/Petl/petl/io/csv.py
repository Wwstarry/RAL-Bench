"""
CSV I/O operations.
"""

import csv


class CSVTable:
    """Lazy wrapper around a CSV file."""
    
    def __init__(self, path):
        self.path = path
    
    def __iter__(self):
        with open(self.path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                yield tuple(row)


def fromcsv(path):
    """
    Load a table from a CSV file.
    
    Returns a lazy table wrapper that reads the CSV when iterated.
    """
    return CSVTable(path)


def tocsv(table, path):
    """
    Write a table to a CSV file.
    
    Materializes the table by iterating through all rows.
    """
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for row in table:
            writer.writerow(row)