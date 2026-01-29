"""
Key-generation helpers.  The real ‘cachetools’ project provides a fairly rich
set of helpers – we just ship the subset that is commonly used by down-stream
code and the test-suite:  `hashkey`.
"""
from typing import Any, Tuple


class _HashedSeq(list):
    """
    A list that behaves like a tuple for hashing purposes.  Copied in spirit
    from the reference ‘cachetools’ implementation.
    """

    __slots__ = ("_hash",)

    def __init__(self, seq):
        super().__init__(seq)
        self._hash = hash(tuple(seq))

    def __hash__(self):  # noqa: D401
        return self._hash


def _flat_kwargs(kwargs) -> Tuple[Any, ...]:
    """
    Convert **kwargs into a stable, hashable tuple.  Sorting is used so that
    argument order does not influence the generated cache-key.
    """
    if not kwargs:  # fast path
        return ()
    return tuple(item for pair in sorted(kwargs.items()) for item in pair)


def hashkey(*args: Any, **kwargs: Any):
    """
    Return a hashable key built from positional + keyword arguments.

    The algorithm is intentionally very similar to the reference implementation:
        • Positional arguments first
        • Followed by each keyword and its value, sorted by keyword
    The returned object is an instance of `_HashedSeq` (list-based) which
    pre-computes its hash for performance and immutability.
    """
    key = args + _flat_kwargs(kwargs)
    return _HashedSeq(key)