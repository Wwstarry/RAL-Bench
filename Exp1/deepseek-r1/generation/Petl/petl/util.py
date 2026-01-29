"""
Utility functions and base classes.
"""
from typing import Iterable, Iterator, List, Union
import collections.abc

Table = Union[Iterable[tuple], 'TableWrapper']

class TableWrapper(collections.abc.Iterable):
    """Base table wrapper implementing lazy iteration."""
    def __init__(self, source: Union[Iterable, callable]):
        if callable(source):
            self._source = source
        else:
            self._source = lambda: iter(source)
    
    def __iter__(self) -> Iterator[tuple]:
        return iter(self._source())

def fromdicts(records: List[dict], header: List[str] = None) -> Table:
    """
    Create table from list of dictionaries.
    
    Args:
        records: List of dictionaries
        header: Optional header list
    
    Returns:
        Table with header and data rows
    """
    def dicts_iterator():
        if not records:
            yield ()
            return
        
        if header is None:
            # Infer header from first dict keys
            header_row = list(records[0].keys())
        else:
            header_row = header
        
        yield tuple(header_row)
        
        for record in records:
            row = tuple(record.get(field) for field in header_row)
            yield row
    
    return TableWrapper(dicts_iterator)

def addfield(table: Table, fieldname: str, func: callable) -> Table:
    """
    Add new field to table.
    
    Args:
        table: Input table
        fieldname: Name of new field
        func: Function to compute field values
    
    Returns:
        Table with added field
    """
    def addfield_iterator():
        it = iter(table)
        header = next(it)
        yield header + (fieldname,)
        
        for row in it:
            new_value = func(row)
            yield row + (new_value,)
    
    return TableWrapper(addfield_iterator)