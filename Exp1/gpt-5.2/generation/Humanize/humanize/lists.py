from __future__ import annotations

from typing import Iterable, List, Sequence, Any, Optional

from .i18n import gettext


def natural_list(
    items: Iterable[Any],
    separator: str = ", ",
    conjunction: str = "and",
    serial_comma: bool = True,
) -> str:
    """
    Convert an iterable into a human-readable list:
      [] -> ''
      ['a'] -> 'a'
      ['a','b'] -> 'a and b'
      ['a','b','c'] -> 'a, b, and c' (serial_comma=True)

    API name in the reference project is `natural_list`.
    """
    lst: List[str] = [str(i) for i in items]
    n = len(lst)
    if n == 0:
        return ""
    if n == 1:
        return lst[0]
    conj = gettext(conjunction)
    if n == 2:
        return f"{lst[0]} {conj} {lst[1]}"
    body = separator.join(lst[:-1])
    if serial_comma:
        return f"{body}{separator}{conj} {lst[-1]}"
    # No Oxford comma: replace last separator with space+conj
    return f"{body} {conj} {lst[-1]}"