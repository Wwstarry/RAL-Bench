def join(left, right, key='id'):
    def joined():
        left_it = iter(left())
        right_it = iter(right())
        left_header = next(left_it)
        right_header = next(right_it)
        left_idx = left_header.index(key)
        right_idx = right_header.index(key)
        combined_header = left_header + [f for i, f in enumerate(right_header) if i != right_idx]
        yield combined_header

        right_rows = {row[right_idx]: row for row in right_it}
        for left_row in left_it:
            if left_row[left_idx] in right_rows:
                right_row = right_rows[left_row[left_idx]]
                combined_row = left_row + [f for i, f in enumerate(right_row) if i != right_idx]
                yield combined_row
    return joined