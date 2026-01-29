"""
Column conversion operations.
"""

from typing import Callable, Iterable, Iterator, Tuple, Any
from ..core import TableWrapper


def convert(table: Iterable, field: str, func: Callable) -> TableWrapper:
    """
    Apply a conversion function to values in a field.
    
    Args:
        table: Input table
        field: Field name to convert
        func: Conversion function
    
    Returns:
        TableWrapper: Table with converted values.
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
        
        # Apply conversion to each row
        for row in iterator:
            row_list = list(row)
            row_list[field_index] = func(row_list[field_index])
            yield tuple(row_list)
    
    return TableWrapper(source)


def addfield(table: Iterable, fieldname: str, func: Callable) -> TableWrapper:
    """
    Add a new field to the table.
    
    Args:
        table: Input table
        fieldname: Name of new field
        func: Function to compute field value from row
    
    Returns:
        TableWrapper: Table with added field.
    """
    def source():
        iterator = iter(table)
        header = next(iterator)
        yield header + (fieldname,)
        
        for row in iterator:
            new_value = func(row)
            yield row + (new_value,)
    
    return TableWrapper(source)