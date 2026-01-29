from __future__ import annotations

import math
from decimal import Decimal
from typing import Any, Optional


def intcomma(value: Any) -> str:
    """
    Convert an integer/float/Decimal/string into a string with commas.

    Compatible with core behavior from the reference humanize project:
    - preserves sign
    - preserves fractional part if provided
    - does not round
    """
    if value is None:
        return "0"

    # Convert to string while preserving given precision when possible.
    if isinstance(value, Decimal):
        s = format(value, "f")
    else:
        s = str(value)

    s = s.strip()
    if not s:
        return "0"

    sign = ""
    if s[0] in "+-":
        sign, s = s[0], s[1:]

    # Handle scientific notation by converting to Decimal.
    if "e" in s.lower():
        try:
            d = Decimal(sign + s)
            s = format(d, "f")
            sign = ""
            if s and s[0] in "+-":
                sign, s = s[0], s[1:]
        except Exception:
            # Fall back to raw string if it can't be parsed.
            s = s

    if "." in s:
        int_part, frac_part = s.split(".", 1)
        frac = "." + frac_part
    else:
        int_part, frac = s, ""

    if int_part == "":
        int_part = "0"

    # If the integer part is not numeric (e.g., "NaN"), return original.
    if not int_part.isdigit():
        return sign + int_part + frac

    n = int_part
    # Insert commas from the right.
    parts = []
    while len(n) > 3:
        parts.append(n[-3:])
        n = n[:-3]
    parts.append(n)
    out_int = ",".join(reversed(parts))
    return f"{sign}{out_int}{frac}"


def ordinal(value: Any) -> str:
    """
    Convert an integer to its ordinal representation: 1 -> 1st, 2 -> 2nd, etc.
    """
    try:
        n = int(value)
    except Exception:
        return str(value)

    abs_n = abs(n)
    if 10 <= (abs_n % 100) <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(abs_n % 10, "th")
    return f"{n}{suffix}"


def _format_number(value: float, digits: int) -> str:
    # Helper used by other modules (kept internal).
    if digits < 0:
        digits = 0
    fmt = f"{{:.{digits}f}}"
    s = fmt.format(value)
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def _to_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(str(value).strip())
    except Exception:
        return None


def _isfinite(x: float) -> bool:
    return math.isfinite(x)