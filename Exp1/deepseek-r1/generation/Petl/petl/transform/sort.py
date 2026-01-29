"""
Sorting operations.
"""
from typing import Union
from ..util import Table, _TableWrapper

def sort(table: Table, field: Union[str, int]) -> Table:
    """
    Sort table by field.
    
    Args:
        table: Input table
        field: Field name or index to sort by
    
    Returns:
        Sorted table
    """
    def sort_iterator():
        it = iter(table)
        header = next(it)
        yield header
        
        # Find field index
        if isinstance(field, str):
            field_index = header.index(field)
        else:
            field_index = field
        
        # Materialize and sort
        rows = list(it)
        rows.sort(key=lambda x: x[field_index])
        for row in rows:
            yield row
    
    return _TableWrapper(sort_iterator)