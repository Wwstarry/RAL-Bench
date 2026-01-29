class JoinView:
    def __init__(self, left, right, key):
        self.left = left
        self.right = right
        self.key = key

    def __iter__(self):
        # Initialize iterators
        lit = iter(self.left)
        rit = iter(self.right)

        try:
            lhdr = next(lit)
        except StopIteration:
            return # Empty left

        try:
            rhdr = next(rit)
        except StopIteration:
            return # Empty right

        # Determine key indices
        # self.key can be a string or list of strings
        if isinstance(self.key, str):
            lkey = self.key
            rkey = self.key
            l_key_indices = [lhdr.index(lkey)]
            r_key_indices = [rhdr.index(rkey)]
        else:
            # Assume list of keys
            l_key_indices = [lhdr.index(k) for k in self.key]
            r_key_indices = [rhdr.index(k) for k in self.key]

        # Build Right Hash Map
        # Map key_tuple -> list of rows
        # We must read the entire right table into memory (standard hash join)
        r_map = {}
        
        # Helper to extract key
        def get_key(row, indices):
            return tuple(row[i] for i in indices)

        for row in rit:
            k = get_key(row, r_key_indices)
            if k not in r_map:
                r_map[k] = []
            r_map[k].append(row)

        # Construct Output Header
        # Standard petl join: Left Header + (Right Header - Keys)
        r_indices_to_keep = [i for i, col in enumerate(rhdr) if i not in r_key_indices]
        out_header = list(lhdr) + [rhdr[i] for i in r_indices_to_keep]
        yield tuple(out_header)

        # Stream Left and Probe
        for lrow in lit:
            k = get_key(lrow, l_key_indices)
            if k in r_map:
                r_rows = r_map[k]
                for rrow in r_rows:
                    # Merge rows
                    r_part = [rrow[i] for i in r_indices_to_keep]
                    yield tuple(list(lrow) + r_part)

def join(left, right, key='id'):
    """
    Perform an inner join between two tables.
    """
    return JoinView(left, right, key)