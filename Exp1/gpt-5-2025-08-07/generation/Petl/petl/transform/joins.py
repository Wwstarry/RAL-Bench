from .. import _field_index


class JoinTable:
    """
    Inner join of two tables on a key field. Duplicates rows for multiple matches.
    """
    def __init__(self, left, right, key="id"):
        self._left = left
        self._right = right
        self._key = key

    def __iter__(self):
        # Prepare left iterator and header
        left_it = iter(self._left)
        left_header = next(left_it)
        # Prepare right iterator and header
        right_it = iter(self._right)
        right_header = next(right_it)

        # Resolve key indices
        left_key_idx = _field_index(left_header, self._key)
        right_key_idx = _field_index(right_header, self._key)

        # Build right index: key -> list of rows
        right_index = {}
        for row in right_it:
            if right_key_idx is None or right_key_idx >= len(row):
                continue
            k = row[right_key_idx]
            right_index.setdefault(k, []).append(tuple(row))

        # Construct output header: left + right (excluding duplicate key from right)
        out_header = list(left_header) + [f for i, f in enumerate(right_header) if i != right_key_idx]
        yield tuple(out_header)

        # Emit joined rows
        for lrow in left_it:
            if left_key_idx is None or left_key_idx >= len(lrow):
                continue
            lk = lrow[left_key_idx]
            matches = right_index.get(lk, [])
            for rrow in matches:
                # Combine rows excluding right key field
                combined = list(lrow) + [v for i, v in enumerate(rrow) if i != right_key_idx]
                yield tuple(combined)


def join(left, right, key="id"):
    """
    Inner join on key field.
    """
    return JoinTable(left, right, key=key)