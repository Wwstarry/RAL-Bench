"""
Number helpers – a *very* small subset of Humanize's full feature-set.
"""

from __future__ import annotations

import decimal
import math
from typing import Any


def _to_decimal(value: Any) -> decimal.Decimal:
    """
    Convert ``value`` to :class:`decimal.Decimal` while keeping exactness for
    integers / strings.  Floats are converted via ``str(value)`` to avoid
    surprising binary floating-point issues.
    """
    if isinstance(value, decimal.Decimal):
        return value
    if isinstance(value, (int,)):
        return decimal.Decimal(value)
    try:
        # Fallback – create from str() to keep floats sane
        return decimal.Decimal(str(value))
    except Exception:
        raise ValueError(f"Unable to convert {value!r} to Decimal")


def intcomma(value: Any, use_l10n: bool | None = None, locale: str | None = None) -> str:  # noqa: D401,E501
    """
    Insert commas into the *integer* part of *value* every three digits.

    Parameters
    ----------
    value
        Any object that can be converted to a number or string representation
        of a number.  Decimals are accepted and preserved.
    use_l10n, locale
        Kept for signature compatibility – they are currently ignored.

    Examples
    --------
    >>> intcomma(1234567)
    '1,234,567'
    >>> intcomma(12345.67)
    '12,345.67'
    """
    value = str(value)
    if not value:
        return ""

    sign = ""
    if value[0] in ("+", "-"):
        sign, value = value[0], value[1:]

    if "." in value:
        int_part, frac_part = value.split(".", 1)
        frac_part = "." + frac_part
    else:
        int_part, frac_part = value, ""

    reversed_digits = int_part[::-1]
    grouped = ",".join(
        reversed_digits[i : i + 3] for i in range(0, len(reversed_digits), 3)
    )
    return f"{sign}{grouped[::-1]}{frac_part}"


def ordinal(value: Any) -> str:
    """
    Turn *value* into an ordinal (1st, 2nd, 3rd, …).

    The algorithm follows English rules:

    * Numbers ending in 11, 12, 13 ⇒ “th”
    * Otherwise 1 ⇒ “st”, 2 ⇒ “nd”, 3 ⇒ “rd”, default ⇒ “th”
    """
    try:
        # Handles int, Decimal, str
        n = int(_to_decimal(value))
    except Exception:  # pragma: no cover
        raise ValueError(f"{value!r} can not be interpreted as an integer")

    suffixes = {1: "st", 2: "nd", 3: "rd"}
    if 10 <= (abs(n) % 100) <= 13:
        suffix = "th"
    else:
        suffix = suffixes.get(abs(n) % 10, "th")
    return f"{n}{suffix}"