def join(left, right, key="id"):
    """
    Inner join on a key field.

    key can be a field name or an integer index, but name is recommended.
    Output fields:
      - all fields from left header
      - plus fields from right header excluding the join key if it duplicates a name
        already present in left (including the key field itself).

    This implementation indexes the right table by key (materializes right side).
    """
    def _iter():
        lit = iter(left)
        rit = iter(right)
        try:
            lhdr = tuple(next(lit))
        except StopIteration:
            return
        try:
            rhdr = tuple(next(rit))
        except StopIteration:
            # right empty: still output combined header and no rows
            yield lhdr
            return

        def resolve(hdr, k):
            if isinstance(k, int):
                return k
            try:
                return hdr.index(k)
            except ValueError:
                raise KeyError(f"field not found: {k!r}")

        lk = resolve(lhdr, key)
        rk = resolve(rhdr, key)

        # compute output header
        left_fields = list(lhdr)
        left_set = set(left_fields)

        right_fields_out = []
        right_map_out = []  # indices in right row to include
        for i, f in enumerate(rhdr):
            if f in left_set:
                # avoid duplicates (includes key and any shared names)
                continue
            right_fields_out.append(f)
            right_map_out.append(i)

        out_hdr = tuple(left_fields + right_fields_out)
        yield out_hdr

        # index right by key
        index = {}
        for rrow in rit:
            rrow = tuple(rrow)
            k = rrow[rk]
            index.setdefault(k, []).append(rrow)

        for lrow in lit:
            lrow = tuple(lrow)
            k = lrow[lk]
            matches = index.get(k)
            if not matches:
                continue
            for rrow in matches:
                extra = tuple(rrow[i] for i in right_map_out)
                yield lrow + extra

    return _iter()