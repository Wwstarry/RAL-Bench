"""
Join operations.
"""
from typing import Union
from ..util import Table, _TableWrapper

def join(left: Table, right: Table, key: Union[str, int] = 'id') -> Table:
    """
    Join two tables on key field.
    
    Args:
        left: Left table
        right: Right table
        key: Field name or index to join on
    
    Returns:
        Joined table
    """
    def join_iterator():
        left_it = iter(left)
        left_header = next(left_it)
        right_it = iter(right)
        right_header = next(right_it)
        
        # Find key indices
        if isinstance(key, str):
            left_key_index = left_header.index(key)
            right_key_index = right_header.index(key)
        else:
            left_key_index = key
            right_key_index = key
        
        # Build lookup from right table
        right_lookup = {}
        for row in right_it:
            key_val = row[right_key_index]
            if key_val not in right_lookup:
                right_lookup[key_val] = []
            right_lookup[key_val].append(row)
        
        # Generate header
        # Remove key from right header to avoid duplicate
        right_header_no_key = right_header[:right_key_index] + right_header[right_key_index+1:]
        yield left_header + right_header_no_key
        
        # Generate rows
        for left_row in left_it:
            key_val = left_row[left_key_index]
            if key_val in right_lookup:
                for right_row in right_lookup[key_val]:
                    right_row_no_key = right_row[:right_key_index] + right_row[right_key_index+1:]
                    yield left_row + right_row_no_key
    
    return _TableWrapper(join_iterator)