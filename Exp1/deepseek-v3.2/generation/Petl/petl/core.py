"""
Core table protocol and basic table constructors.
"""

import itertools
from typing import (
    Iterable, Iterator, List, Tuple, Dict, Any, Callable, Optional, Union
)


class TableWrapper:
    """Lazy table wrapper implementing the table protocol."""
    
    def __init__(self, source: Union[Iterable, Callable[[], Iterator]]):
        """
        Initialize a table wrapper.
        
        Args:
            source: Either an iterable or a callable that returns an iterator.
                   If an iterable, it will be converted to an iterator.
        """
        if callable(source):
            self._source_factory = source
        else:
            def factory():
                return iter(source)
            self._source_factory = factory
    
    def __iter__(self) -> Iterator:
        """Return an iterator over the table rows."""
        return self._source_factory()
    
    def __repr__(self) -> str:
        """Return a string representation of the table."""
        # Materialize first few rows for display
        rows = []
        iterator = iter(self)
        for i, row in enumerate(iterator):
            rows.append(row)
            if i >= 4:  # Show at most 5 rows
                break
        return f"<TableWrapper with {len(rows)} rows shown>"
    
    def _materialize(self) -> List[Tuple]:
        """Materialize the entire table as a list of tuples."""
        return list(self)


def fromdicts(records: Iterable[Dict], header: Optional[List[str]] = None) -> TableWrapper:
    """
    Create a table from an iterable of dictionaries.
    
    Args:
        records: Iterable of dictionaries
        header: Optional list of field names. If not provided, uses union of all keys.
    
    Returns:
        TableWrapper: A table with the specified header and data rows.
    """
    def source():
        # First pass: collect records and determine header if needed
        recs = list(records)
        
        if header is None:
            # Determine header from union of all keys
            all_keys = set()
            for rec in recs:
                all_keys.update(rec.keys())
            actual_header = list(sorted(all_keys))
        else:
            actual_header = header
        
        # Yield header
        yield tuple(actual_header)
        
        # Yield data rows
        for rec in recs:
            row = tuple(rec.get(field) for field in actual_header)
            yield row
    
    return TableWrapper(source)