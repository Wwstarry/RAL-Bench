"""
Join operations.
"""


class JoinTable:
    """Lazy table that performs an inner join on two tables."""
    
    def __init__(self, left, right, key):
        self.left = left
        self.right = right
        self.key = key
    
    def __iter__(self):
        # Materialize both tables
        left_it = iter(self.left)
        left_header = next(left_it)
        left_rows = list(left_it)
        
        right_it = iter(self.right)
        right_header = next(right_it)
        right_rows = list(right_it)
        
        # Find key indices
        try:
            left_key_idx = left_header.index(self.key)
        except ValueError:
            raise ValueError(f"Key '{self.key}' not found in left table header")
        
        try:
            right_key_idx = right_header.index(self.key)
        except ValueError:
            raise ValueError(f"Key '{self.key}' not found in right table header")
        
        # Build output header
        # Include all fields from left, then all fields from right except the key
        output_header = list(left_header)
        for field in right_header:
            if field != self.key:
                output_header.append(field)
        yield tuple(output_header)
        
        # Build index for right table
        right_index = {}
        for row in right_rows:
            key_value = row[right_key_idx]
            if key_value not in right_index:
                right_index[key_value] = []
            right_index[key_value].append(row)
        
        # Perform join
        for left_row in left_rows:
            left_key_value = left_row[left_key_idx]
            if left_key_value in right_index:
                for right_row in right_index[left_key_value]:
                    # Combine rows: all of left + all of right except key
                    output_row = list(left_row)
                    for i, value in enumerate(right_row):
                        if i != right_key_idx:
                            output_row.append(value)
                    yield tuple(output_row)


def join(left, right, key='id'):
    """
    Perform an inner join on two tables.
    
    Returns a lazy table wrapper (though join requires materialization).
    """
    return JoinTable(left, right, key)