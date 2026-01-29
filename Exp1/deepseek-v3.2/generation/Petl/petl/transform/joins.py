"""
Join operations.
"""

from typing import Iterable, Iterator, Tuple, Any, Dict, List, Set
from ..core import TableWrapper


def join(left: Iterable, right: Iterable, key: str = 'id') -> TableWrapper:
    """
    Join two tables on a key field.
    
    Args:
        left: Left table
        right: Right table
        key: Field name to join on
    
    Returns:
        TableWrapper: Joined table.
    """
    def source():
        left_iter = iter(left)
        right_iter = iter(right)
        
        # Get headers
        left_header = next(left_iter)
        right_header = next(right_iter)
        
        # Find key indices
        try:
            left_key_idx = left_header.index(key)
        except ValueError:
            raise ValueError(f"Key field '{key}' not found in left header: {left_header}")
        
        try:
            right_key_idx = right_header.index(key)
        except ValueError:
            raise ValueError(f"Key field '{key}' not found in right header: {right_header}")
        
        # Build index from right table
        right_index: Dict[Any, List[Tuple]] = {}
        for right_row in right_iter:
            key_value = right_row[right_key_idx]
            if key_value not in right_index:
                right_index[key_value] = []
            right_index[key_value].append(right_row)
        
        # Create output header
        # Remove key from right header to avoid duplicate
        right_header_no_key = tuple(f for i, f in enumerate(right_header) if i != right_key_idx)
        output_header = left_header + right_header_no_key
        yield output_header
        
        # Determine indices for right fields in output
        right_field_indices = [i for i in range(len(right_header)) if i != right_key_idx]
        
        # Perform join
        for left_row in left_iter:
            key_value = left_row[left_key_idx]
            if key_value in right_index:
                for right_row in right_index[key_value]:
                    # Build output row
                    output_row = left_row
                    for idx in right_field_indices:
                        output_row += (right_row[idx],)
                    yield output_row
    
    return TableWrapper(source)