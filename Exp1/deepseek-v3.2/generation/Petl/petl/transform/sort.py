"""
Sorting operations.
"""

from typing import Iterable, Iterator, Tuple, Any, List
from ..core import TableWrapper


def sort(table: Iterable, field: str) -> TableWrapper:
    """
    Sort table by field.
    
    Note: This implementation materializes the table for sorting.
    
    Args:
        table: Input table
        field: Field name to sort by
    
    Returns:
        TableWrapper: Sorted table.
    """
    def source():
        iterator = iter(table)
        header = next(iterator)
        yield header
        
        # Find field index
        try:
            field_index = header.index(field)
        except ValueError:
            raise ValueError(f"Field '{field}' not found in header: {header}")
        
        # Materialize and sort
        rows = list(iterator)
        rows.sort(key=lambda row: row[field_index])
        
        for row in rows:
            yield row
    
    return TableWrapper(source)