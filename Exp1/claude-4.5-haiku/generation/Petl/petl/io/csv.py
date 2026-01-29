"""
CSV I/O operations.
"""

import csv
from petl.table import Table


class CSVTable(Table):
    """Table that reads from a CSV file."""
    
    def __init__(self, path, encoding='utf-8', **kwargs):
        self.path = path
        self.encoding = encoding
        self.csv_kwargs = kwargs
    
    def __iter__(self):
        with open(self.path, 'r', encoding=self.encoding, newline='') as f:
            reader = csv.reader(f, **self.csv_kwargs)
            for row in reader:
                yield row


def fromcsv(path, encoding='utf-8', **kwargs):
    """
    Create a table from a CSV file.
    
    Args:
        path: Path to the CSV file
        encoding: File encoding (default: 'utf-8')
        **kwargs: Additional arguments passed to csv.reader
    
    Returns:
        A Table object
    """
    return CSVTable(path, encoding=encoding, **kwargs)


def tocsv(table, path, encoding='utf-8', **kwargs):
    """
    Write a table to a CSV file.
    
    Args:
        table: A Table object or iterable
        path: Path to write the CSV file
        encoding: File encoding (default: 'utf-8')
        **kwargs: Additional arguments passed to csv.writer
    
    Returns:
        None
    """
    with open(path, 'w', encoding=encoding, newline='') as f:
        writer = csv.writer(f, **kwargs)
        for row in table:
            writer.writerow(row)