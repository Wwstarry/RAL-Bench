"""
Join operations.
"""

from petl.table import Table


class JoinTable(Table):
    """Table that performs an inner join on two tables."""
    
    def __init__(self, left, right, key='id', lkey=None, rkey=None):
        self.left = left
        self.right = right
        self.key = key
        self.lkey = lkey if lkey is not None else key
        self.rkey = rkey if rkey is not None else key
    
    def __iter__(self):
        # Read left table
        left_iter = iter(self.left)
        left_header = next(left_iter)
        left_rows = list(left_iter)
        
        # Read right table
        right_iter = iter(self.right)
        right_header = next(right_iter)
        right_rows = list(right_iter)
        
        # Find key indices
        try:
            left_key_index = left_header.index(self.lkey)
        except ValueError:
            raise ValueError(f"Key '{self.lkey}' not found in left table")
        
        try:
            right_key_index = right_header.index(self.rkey)
        except ValueError:
            raise ValueError(f"Key '{self.rkey}' not found in right table")
        
        # Build index for right table
        right_index = {}
        for right_row in right_rows:
            key_value = right_row[right_key_index]
            if key_value not in right_index:
                right_index[key_value] = []
            right_index[key_value].append(right_row)
        
        # Create output header
        # Include all left fields, then right fields except the join key
        output_header = list(left_header)
        for i, field in enumerate(right_header):
            if i != right_key_index:
                output_header.append(field)
        
        yield output_header
        
        # Perform join
        for left_row in left_rows:
            left_key_value = left_row[left_key_index]
            if left_key_value in right_index:
                for right_row in right_index[left_key_value]:
                    # Combine rows
                    output_row = list(left_row)
                    for i, value in enumerate(right_row):
                        if i != right_key_index:
                            output_row.append(value)
                    yield output_row


def join(left, right, key='id', lkey=None, rkey=None):
    """
    Perform an inner join on two tables.
    
    Args:
        left: Left table
        right: Right table
        key: The join key (used for both tables if lkey/rkey not specified)
        lkey: Left table key (overrides key)
        rkey: Right table key (overrides key)
    
    Returns:
        A new Table object
    """
    return JoinTable(left, right, key=key, lkey=lkey, rkey=rkey)