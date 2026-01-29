"""
CSV I/O operations for the ETL library.
"""
import csv
from typing import Iterable, Iterator, List, Union, TextIO
from ..util import Table

def fromcsv(path: str, delimiter: str = ',', encoding: str = 'utf-8') -> Table:
    """
    Extract table from CSV file.
    
    Args:
        path: Path to CSV file
        delimiter: Field delimiter character
        encoding: File encoding
    
    Returns:
        Table iterator with first row as header
    """
    def csv_iterator():
        with open(path, 'r', encoding=encoding) as f:
            reader = csv.reader(f, delimiter=delimiter)
            for row in reader:
                yield tuple(row)
    
    return _TableWrapper(csv_iterator)

def tocsv(table: Table, path: str, delimiter: str = ',', encoding: str = 'utf-8') -> None:
    """
    Load table to CSV file.
    
    Args:
        table: Table to write
        path: Output file path
        delimiter: Field delimiter character
        encoding: File encoding
    """
    with open(path, 'w', newline='', encoding=encoding) as f:
        writer = csv.writer(f, delimiter=delimiter)
        for row in table:
            writer.writerow(row)

class _TableWrapper:
    """Internal table wrapper implementing lazy iteration."""
    def __init__(self, source: Union[Iterable, callable]):
        if callable(source):
            self._source = source
        else:
            self._source = lambda: iter(source)
    
    def __iter__(self) -> Iterator[tuple]:
        return iter(self._source())