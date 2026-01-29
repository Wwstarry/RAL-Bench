"""
Row selection operations.
"""

from typing import Callable, Iterable, Iterator, Tuple, Any
from ..core import TableWrapper


def select(table: Iterable, predicate: Callable[[Tuple], bool]) -> TableWrapper:
    """
    Select rows where predicate returns True.
    
    Args:
        table: Input table
        predicate: Function that takes a row and returns bool
    
    Returns:
        TableWrapper: Table with selected rows.
    """
    def source():
        iterator = iter(table)
        header = next(iterator)
        yield header
        
        for row in iterator:
            if predicate(row):
                yield row
    
    return TableWrapper(source)


def selectge(table: Iterable, field: str, threshold: Any) -> TableWrapper:
    """
    Select rows where field >= threshold.
    
    Args:
        table: Input table
        field: Field name to compare
        threshold: Threshold value
    
    Returns:
        TableWrapper: Table with selected rows.
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
        
        for row in iterator:
            if row[field_index] >= threshold:
                yield row
    
    return TableWrapper(source)


def selectgt(table: Iterable, field: str, threshold: Any) -> TableWrapper:
    """
    Select rows where field > threshold.
    
    Args:
        table: Input table
        field: Field name to compare
        threshold: Threshold value
    
    Returns:
        TableWrapper: Table with selected rows.
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
        
        for row in iterator:
            if row[field_index] > threshold:
                yield row
    
    return TableWrapper(source)