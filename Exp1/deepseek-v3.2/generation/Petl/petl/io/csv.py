"""
CSV I/O operations.
"""

import csv
from typing import Iterator, Tuple, Iterable
from ..core import TableWrapper


def fromcsv(path: str, **kwargs) -> TableWrapper:
    """
    Create a table from a CSV file.
    
    Args:
        path: Path to CSV file
        **kwargs: Additional arguments passed to csv.reader
    
    Returns:
        TableWrapper: A table with CSV data.
    """
    def source():
        with open(path, 'r', newline='') as f:
            reader = csv.reader(f, **kwargs)
            for row in reader:
                yield tuple(row)
    
    return TableWrapper(source)


def tocsv(table: Iterable, path: str, **kwargs) -> None:
    """
    Write a table to a CSV file.
    
    Args:
        table: Table to write
        path: Path to output CSV file
        **kwargs: Additional arguments passed to csv.writer
    """
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f, **kwargs)
        for row in table:
            writer.writerow(row)