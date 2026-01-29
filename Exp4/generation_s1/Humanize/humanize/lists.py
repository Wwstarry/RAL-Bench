from __future__ import annotations

from typing import Iterable, Optional, Sequence, Any


def natural_list(
    iterable: Iterable[Any],
    separator: str = ", ",
    conjunction: str = "and",
    final_separator: Optional[str] = None,
    oxford_comma: bool = True,
) -> str:
    items = [str(x) for x in iterable]
    n = len(items)
    if n == 0:
        return ""
    if n == 1:
        return items[0]
    if n == 2:
        return f"{items[0]} {conjunction} {items[1]}"

    if final_separator is None:
        if oxford_comma:
            final_separator = f"{separator}{conjunction} "
        else:
            final_separator = f" {conjunction} "

    head = separator.join(items[:-1])
    return f"{head}{final_separator}{items[-1]}"