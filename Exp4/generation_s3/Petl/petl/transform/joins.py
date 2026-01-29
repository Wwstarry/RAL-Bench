def _resolve_field_index(header, field):
    if isinstance(field, int):
        if field < 0 or field >= len(header):
            raise IndexError(field)
        return field
    try:
        return header.index(field)
    except ValueError:
        raise KeyError(field)


class JoinView:
    """
    Inner equi-join on a single key field.

    Indexes the right table (materialized) and streams the left table.
    """

    def __init__(self, left, right, key="id"):
        self.left = left
        self.right = right
        self.key = key

    def __iter__(self):
        lit = iter(self.left)
        rit = iter(self.right)

        try:
            lhdr = next(lit)
        except StopIteration:
            return
            yield  # pragma: no cover
        try:
            rhdr = next(rit)
        except StopIteration:
            return
            yield  # pragma: no cover

        lhdr = tuple(lhdr)
        rhdr = tuple(rhdr)

        lk = _resolve_field_index(lhdr, self.key)
        rk = _resolve_field_index(rhdr, self.key)

        # Build output header: left header + right header excluding right key.
        out_hdr = list(lhdr) + [f for i, f in enumerate(rhdr) if i != rk]
        yield tuple(out_hdr)

        # Index right side by key value -> list of right rows
        r_index = {}
        for r in rit:
            rt = tuple(r)
            k = rt[rk]
            r_index.setdefault(k, []).append(rt)

        # Stream left; for each match on right, emit combined row.
        for l in lit:
            lt = tuple(l)
            k = lt[lk]
            matches = r_index.get(k)
            if not matches:
                continue
            for rt in matches:
                combined = list(lt) + [v for i, v in enumerate(rt) if i != rk]
                yield tuple(combined)


def join(left, right, key="id"):
    """Inner join left and right tables on key (name or index)."""
    return JoinView(left, right, key=key)