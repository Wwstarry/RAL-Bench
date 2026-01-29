"""
Very small inner-join implementation.
"""

from .. import Table
from .conversions import _field_index


def join(left, right, key="id"):
    """
    Inner join between *left* and *right* tables on *key*.

    Only rows that have matching key values in **both** tables are kept.
    """

    def _factory():
        # prepare headers and index positions
        li = iter(left)
        ri = iter(right)

        try:
            lhdr = next(li)
            rhdr = next(ri)
        except StopIteration:
            return iter([])  # at least one table empty

        lidx = _field_index(lhdr, key)
        ridx = _field_index(rhdr, key)

        # build right-hand lookup (allow multiple hits)
        lookup = {}
        for r in ri:
            k = r[ridx]
            lookup.setdefault(k, []).append(r)

        # build output header (avoid duplicate key)
        combined_hdr = tuple(list(lhdr) + [f for i, f in enumerate(rhdr) if i != ridx])
        yield combined_hdr

        # iterate left and match
        for lrow in li:
            k = lrow[lidx]
            matches = lookup.get(k)
            if not matches:
                continue
            base_left = list(lrow)
            for rrow in matches:
                combined = base_left + [v for i, v in enumerate(rrow) if i != ridx]
                yield tuple(combined)

    return Table(_factory)