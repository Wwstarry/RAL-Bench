def join(left, right, key="id"):
    """
    Inner join of two tables on key.

    key may be a field name (str) or index (int). If str, it is resolved against
    each table's header. Result header includes all left fields plus right fields
    excluding the key field (if present as a name in right).
    """

    class _JoinTable:
        def __init__(self, l, r, k):
            self._left = l
            self._right = r
            self._key = k

        def __iter__(self):
            lit = iter(self._left)
            rit = iter(self._right)
            lhdr = tuple(next(lit))
            rhdr = tuple(next(rit))

            # resolve key indices
            if isinstance(self._key, int):
                lk = self._key
                rk = self._key
                keyname = None
            else:
                keyname = self._key
                try:
                    lk = lhdr.index(keyname)
                except ValueError:
                    raise KeyError(keyname)
                try:
                    rk = rhdr.index(keyname)
                except ValueError:
                    raise KeyError(keyname)

            # output header: all left + right without duplicate key field name
            if keyname is not None:
                rfields = [f for i, f in enumerate(rhdr) if i != rk]
            else:
                # if joining by index only, avoid duplicating the column at that index
                rfields = [f for i, f in enumerate(rhdr) if i != rk]
            out_header = tuple(lhdr) + tuple(rfields)
            yield out_header

            # build index of right side on join key (materialize right, typical join impl)
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
                    out = list(lrow)
                    out.extend(rrow[i] for i in range(len(rhdr)) if i != rk)
                    yield tuple(out)

    return _JoinTable(left, right, key)