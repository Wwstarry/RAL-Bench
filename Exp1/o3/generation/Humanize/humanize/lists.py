"""
List helpers – English only, minimal implementation.
"""

from __future__ import annotations

from typing import Iterable, List


def _stringify(obj) -> str:
    return str(obj)


def natural_join(
    seq: Iterable[object], sep: str = ", ", conjunction: str = "and"
) -> str:
    """
    Join *seq* similarly to Oxford-comma English:

    >>> natural_join(['a', 'b', 'c'])
    'a, b and c'
    """
    items: List[str] = [_stringify(x) for x in seq]

    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f" {conjunction} ".join(items)
    return f"{sep.join(items[:-1])}{sep}{conjunction} {items[-1]}"


def natural_list(seq: Iterable[object], **kwargs) -> str:  # noqa: D401
    """
    Alias for :func:`natural_join` – kept for API compatibility.
    """
    return natural_join(seq, **kwargs)