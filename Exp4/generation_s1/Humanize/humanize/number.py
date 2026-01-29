from __future__ import annotations

from decimal import Decimal
from typing import Any


def intcomma(value: Any) -> str:
    """
    Convert an integer (or integer-like string) to a string with commas.

    - Preserves sign
    - Commas only applied to integer part; fractional part is preserved
    - For digit strings, preserves leading zeros via direct grouping
    """
    if value is None:
        raise ValueError("intcomma() requires a value")

    # Fast paths for numeric types
    if isinstance(value, bool):
        # bool is an int subclass, but not meaningful here
        value = int(value)

    if isinstance(value, int):
        s = str(value)
        sign = ""
        if s.startswith("-"):
            sign, s = "-", s[1:]
        return sign + _group_digits(s)

    if isinstance(value, (float, Decimal)):
        s = format(value, "f")
        return intcomma(s)

    # String-ish path
    s = str(value).strip()
    if not s:
        raise ValueError("invalid numeric string")

    sign = ""
    if s[0] in "+-":
        sign, s = s[0], s[1:]
    # support a single dot; keep fractional part untouched
    if s.count(".") > 1:
        raise ValueError("invalid numeric string")
    if "." in s:
        intpart, frac = s.split(".", 1)
        if intpart == "":
            intpart = "0"
        if not intpart.isdigit() or (frac and not frac.isdigit()):
            raise ValueError("invalid numeric string")
        return sign + _group_digits(intpart) + "." + frac
    else:
        if not s.isdigit():
            raise ValueError("invalid numeric string")
        return sign + _group_digits(s)


def _group_digits(digits: str) -> str:
    # Group from the right into 3-digit chunks, preserving leading zeros.
    n = len(digits)
    if n <= 3:
        return digits
    first = n % 3
    parts = []
    if first:
        parts.append(digits[:first])
    for i in range(first, n, 3):
        parts.append(digits[i : i + 3])
    return ",".join(parts)


def ordinal(value: Any) -> str:
    """
    Convert an integer to its ordinal as a string: 1 -> "1st", 2 -> "2nd", etc.
    """
    if value is None:
        raise ValueError("ordinal() requires a value")
    try:
        n = int(value)
    except Exception as e:
        raise ValueError("ordinal() requires an integer-like value") from e

    sign = "-" if n < 0 else ""
    absn = abs(n)

    # Teens are special
    if 10 <= (absn % 100) <= 20:
        suffix = "th"
    else:
        last = absn % 10
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(last, "th")
    return f"{sign}{absn}{suffix}"