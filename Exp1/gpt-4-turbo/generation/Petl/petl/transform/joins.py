class JoinTable:
    def __init__(self, left, right, key='id'):
        self.left = left
        self.right = right
        self.key = key

    def __iter__(self):
        # Materialize right table into a dict for join
        left_it = iter(self.left)
        right_it = iter(self.right)
        left_header = next(left_it)
        right_header = next(right_it)

        try:
            left_idx = left_header.index(self.key)
        except ValueError:
            raise Exception(f"Join key '{self.key}' not found in left header")
        try:
            right_idx = right_header.index(self.key)
        except ValueError:
            raise Exception(f"Join key '{self.key}' not found in right header")

        # Build right lookup dict: key -> row
        right_lookup = {}
        for row in right_it:
            k = row[right_idx]
            right_lookup[k] = row

        # Compose output header
        out_header = list(left_header)
        # Add right fields except the join key
        for i, f in enumerate(right_header):
            if i != right_idx:
                out_header.append(f)
        yield tuple(out_header)

        # For each left row, join with right row if key matches
        for lrow in left_it:
            k = lrow[left_idx]
            rrow = right_lookup.get(k)
            if rrow is not None:
                # Compose output row: left fields + right fields (except key)
                out_row = list(lrow)
                for i, v in enumerate(rrow):
                    if i != right_idx:
                        out_row.append(v)
                yield tuple(out_row)

def join(left, right, key='id'):
    """
    Inner join two tables on key.
    """
    return JoinTable(left, right, key)