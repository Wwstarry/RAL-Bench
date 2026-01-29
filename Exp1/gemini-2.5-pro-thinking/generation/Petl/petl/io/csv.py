# petl/io/csv.py

import csv

def fromcsv(path):
    """
    Extract a table from a CSV file.
    """
    with open(path, 'r', newline='') as f:
        reader = csv.reader(f)
        yield from reader

def tocsv(table, path):
    """
    Write a table to a CSV file.
    """
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(table)