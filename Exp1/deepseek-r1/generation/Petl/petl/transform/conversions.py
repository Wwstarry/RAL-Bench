"""
Column conversion operations.
"""
from typing import Callable, Union
from ..util import Table, _TableWrapper

def convert(table: Table, field: Union[str, int], func: Callable) -> Table:
    """
    Transform column values using given function.
    
    Args:
        table: Input table
        field: Field name or index to convert
        func: Conversion function
    
    Returns:
        New table with converted column
    """
    def convert_iterator():
        it = iter(table)
        header = next(it)
        yield header
        
        # Find field index
        if isinstance(field, str):
            try:
                field_index = header.index(field)
            except ValueError:
                raise ValueError(f"Field '{field}' not found in header")
        else:
            field_index = field
        
        for row in it:
            row = list(row)
            row[field_index] = func(row[field_index])
            yield tuple(row)
    
    return _TableWrapper(convert_iterator)