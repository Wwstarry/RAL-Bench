def join(left, right, key='id'):
    """
    Perform an inner join of 'left' and 'right' tables on the given key.
    The resulting table's header is the union of both tables' headers,
    with the join field included once.
    """
    return _JoinTable(left, right, key)

class _JoinTable:
    def __init__(self, left, right, key):
        self.left = left
        self.right = right
        self.key = key

    def __iter__(self):
        it_left = iter(self.left)
        left_header = next(it_left)

        it_right = iter(self.right)
        right_header = next(it_right)

        # Find key index in left and right
        if isinstance(self.key, int):
            left_key_index = self.key
            right_key_index = self.key
            key_name = left_header[left_key_index]
        else:
            left_key_index = left_header.index(self.key)
            right_key_index = right_header.index(self.key)
            key_name = self.key

        # Build a dictionary from right table keyed by the join field
        right_dict = {}
        for row in it_right:
            k = row[right_key_index]
            if k not in right_dict:
                right_dict[k] = []
            right_dict[k].append(row)

        # Build joined header: all of left_header plus the right_header fields except the join key
        joined_header = list(left_header)
        for f in right_header:
            if f != key_name:
                joined_header.append(f)

        yield joined_header

        # Now iterate left table and yield joined rows
        for left_row in it_left:
            left_key_value = left_row[left_key_index]
            if left_key_value in right_dict:
                # For each matching row in right
                for right_row in right_dict[left_key_value]:
                    # Combine: left fields + right fields except the key
                    combined = list(left_row)
                    # Add the right fields except the join key
                    for i, field_name in enumerate(right_header):
                        if i != right_key_index:
                            combined.append(right_row[i])
                    yield combined