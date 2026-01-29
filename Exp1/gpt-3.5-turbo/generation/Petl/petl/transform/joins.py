class JoinTable:
    def __init__(self, left, right, key='id'):
        self.left = left
        self.right = right
        self.key = key

    def __iter__(self):
        left_it = iter(self.left)
        right_it = iter(self.right)

        left_header = next(left_it)
        right_header = next(right_it)

        try:
            left_key_idx = left_header.index(self.key)
        except ValueError:
            left_key_idx = None
        try:
            right_key_idx = right_header.index(self.key)
        except ValueError:
            right_key_idx = None

        # Build right lookup dict: key -> list of rows
        right_map = {}
        for row in right_it:
            if right_key_idx is None:
                continue
            k = row[right_key_idx]
            right_map.setdefault(k, []).append(row)

        # Compose header: left fields + right fields except key
        right_fields_ex_key = [f for i, f in enumerate(right_header) if i != right_key_idx]
        joined_header = tuple(left_header) + tuple(right_fields_ex_key)
        yield joined_header

        for lrow in left_it:
            if left_key_idx is None:
                # no key in left, yield row with right fields empty
                yield tuple(lrow) + tuple(None for _ in right_fields_ex_key)
                continue
            lkey = lrow[left_key_idx]
            matches = right_map.get(lkey)
            if matches:
                for rrow in matches:
                    # exclude key field from right row
                    rvals = tuple(rrow[i] for i in range(len(rrow)) if i != right_key_idx)
                    yield tuple(lrow) + rvals
            else:
                # no match, pad with None for right fields
                yield tuple(lrow) + tuple(None for _ in right_fields_ex_key)

def join(left, right, key='id'):
    """
    Join two tables on key field (inner join semantics with left rows always present).
    """
    return JoinTable(left, right, key)