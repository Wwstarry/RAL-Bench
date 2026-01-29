from __future__ import annotations

from typing import Iterable, Any


def naturallist(seq: Iterable[Any], separator: str = ", ", conjunction: str = "and") -> str:
    if seq is None:
        raise TypeError("seq must not be None")

    items = [str(x) for x in seq]
    n = len(items)
    if n == 0:
        return ""
    if n == 1:
        return items[0]
    if n == 2:
        return f"{items[0]} {conjunction} {items[1]}"
    return f"{separator.join(items[:-1])} {conjunction} {items[-1]}"