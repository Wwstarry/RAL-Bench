"""
Table join operations.
"""

def join(left, right, key='id'):
    """Join two tables on specified key field."""
    def _join_rows():
        left_it = iter(left)
        right_it = iter(right)
        
        left_header = next(left_it)
        right_header = next(right_it)
        
        if key not in left_header:
            raise ValueError(f"Key '{key}' not found in left table header: {left_header}")
        if key not in right_header:
            raise ValueError(f"Key '{key}' not found in right table header: {right_header}")
        
        # Build combined header, avoiding duplicate key
        left_key_index = left_header.index(key)
        right_key_index = right_header.index(key)
        
        # Create new header with key first, then other left fields, then other right fields
        new_header = [key]
        new_header.extend([f for f in left_header if f != key])
        new_header.extend([f for f in right_header if f != key])
        yield new_header
        
        # Materialize right table for lookup
        right_data = {}
        for right_row in right_it:
            if len(right_row) > right_key_index:
                key_value = right_row[right_key_index]
                if key_value not in right_data:
                    right_data[key_value] = []
                right_data[key_value].append(right_row)
        
        # Process left table and join
        for left_row in left_it:
            if len(left_row) > left_key_index:
                key_value = left_row[left_key_index]
                if key_value in right_data:
                    for right_row in right_data[key_value]:
                        # Build joined row: key, left fields (except key), right fields (except key)
                        joined_row = [key_value]
                        
                        # Add left fields except key
                        for i, value in enumerate(left_row):
                            if i != left_key_index:
                                joined_row.append(value)
                        
                        # Add right fields except key
                        for i, value in enumerate(right_row):
                            if i != right_key_index:
                                joined_row.append(value)
                        
                        yield joined_row
    
    from ..core import Table
    return Table(_join_rows())