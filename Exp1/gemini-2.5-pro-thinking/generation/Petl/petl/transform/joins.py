# petl/transform/joins.py

from collections import defaultdict

def join(left, right, key='id'):
    """
    Perform an inner join on two tables. This operation materializes the right table.
    """
    left_it = iter(left)
    right_it = iter(right)

    try:
        left_header = tuple(next(left_it))
        right_header = tuple(next(right_it))
    except StopIteration:
        # If either table is completely empty (no header), the join is empty.
        return

    try:
        left_key_index = left_header.index(key)
        right_key_index = right_header.index(key)
    except ValueError:
        raise ValueError(f"Join key not found: {repr(key)}")

    # Construct the output header
    right_fields_indices = [i for i, h in enumerate(right_header) if h != key]
    new_header = left_header + tuple(right_header[i] for i in right_fields_indices)
    yield new_header

    # Materialize the right table into a lookup dictionary
    right_lookup = defaultdict(list)
    for right_row in right_it:
        key_val = right_row[right_key_index]
        other_vals = tuple(right_row[i] for i in right_fields_indices)
        right_lookup[key_val].append(other_vals)

    if not right_lookup:
        return  # No data rows in right table, so join is empty.

    # Stream the left table and join against the lookup
    for left_row in left_it:
        key_val = left_row[left_key_index]
        if key_val in right_lookup:
            for right_vals in right_lookup[key_val]:
                yield left_row + right_vals