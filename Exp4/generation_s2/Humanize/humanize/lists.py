from __future__ import annotations

from typing import Iterable, List, Sequence


def natural_list(
    items: Iterable[object],
    separator: str = ", ",
    conjunction: str = "and",
) -> str:
    """
    Join items into a natural-language list:
    - [] -> ''
    - ['a'] -> 'a'
    - ['a','b'] -> 'a and b'
    - ['a','b','c'] -> 'a, b and c'
    """
    seq = [str(x) for x in items]
    if not seq:
        return ""
    if len(seq) == 1:
        return seq[0]
    if len(seq) == 2:
        return f"{seq[0]} {conjunction} {seq[1]}"
    return f"{separator.join(seq[:-1])} {conjunction} {seq[-1]}"