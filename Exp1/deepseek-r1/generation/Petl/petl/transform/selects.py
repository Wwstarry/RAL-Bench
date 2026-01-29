"""
Row selection operations.
"""
from typing import Callable, Union
from ..util import Table, _TableWrapper

def select(table: Table, predicate: Callable[[tuple], bool]) -> Table:
    """
    Filter rows using predicate function.
    
    Args:
        table: Input table
        predicate: Function returning True for rows to keep
    
    Returns:
        Filtered table
    """
    def select_iterator():
        it = iter(table)
        header = next(it)
        yield header
        for row in it:
            if predicate(row):
                yield row
    
    return _TableWrapper(select_iterator)

def selectge(table: Table, field: Union[str, int], threshold) -> Table:
    """
    Select rows where field >= threshold.
    
    Args:
        table: Input table
        field: Field name or index
        threshold: Minimum value
    
    Returns:
        Filtered table
    """
    def predicate(row):
        if isinstance(field, str):
            header = next(iter(table))
            field_index = header.index(field)
            # Reset iterator
            it = iter(table)
            next(it)
        else:
            field_index = field
        return row[field_index] >= threshold
    
    return select(table, predicate)

def selectgt(table: Table, field: Union[str, int], threshold) -> Table:
    """
    Select rows where field > threshold.
    
    Args:
        table: Input table
        field: Field name or index
        threshold: Comparison value
    
    Returns:
        Filtered table
    """
    def predicate(row):
        if isinstance(field, str):
            header = next(iter(table))
            field_index = header.index(field)
            # Reset iterator
            it = iter(table)
            next(it)
        else:
            field_index = field
        return row[field_index] > threshold
    
    return select(table, predicate)