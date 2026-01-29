from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Optional


def _to_decimal_str(value: Any) -> Optional[str]:
    """
    Convert common numeric inputs to a non-scientific decimal string.

    Returns None if conversion is not possible.
    """
    if value is None:
        raise TypeError("value must not be None")

    if isinstance(value, Decimal):
        s = format(value, "f")
        return s

    if isinstance(value, (int,)):
        return str(value)

    if isinstance(value, float):
        # Use Decimal(str(x)) to avoid binary float artifacts and scientific
        # notation for typical values.
        try:
            d = Decimal(str(value))
        except Exception:
            return str(value)
        return format(d, "f")

    if isinstance(value, str):
        s = value.strip()
        if not s:
            return value
        # Attempt Decimal parsing for e/E and for numeric strings generally.
        try:
            d = Decimal(s)
        except (InvalidOperation, ValueError):
            return None
        # Preserve fraction digits from the original string when ndigits is None
        # is handled by intcomma; here just return a normalized fixed string.
        return format(d, "f")

    # Fallback: try Decimal on stringified value.
    try:
        d = Decimal(str(value))
    except Exception:
        return None
    return format(d, "f")


def intcomma(value: Any, ndigits: Optional[int] = None) -> str:
    """
    Insert commas into the integer part of a number.

    If ndigits is provided, the value is rounded to that number of decimal places.
    """
    if value is None:
        raise TypeError("value must not be None")

    # Preserve string fractional part when ndigits is None.
    if isinstance(value, str) and ndigits is None:
        s = value.strip()
        if not s:
            return value
        # If scientific notation, try Decimal conversion to a fixed representation.
        if "e" in s.lower():
            try:
                s = format(Decimal(s), "f")
            except Exception:
                return value
        # Now operate on the (possibly) decimal string.
        sign = ""
        if s.startswith(("+", "-")):
            sign = "-" if s[0] == "-" else ""
            s = s[1:]
        if "." in s:
            intpart, fracpart = s.split(".", 1)
            frac = "." + fracpart
        else:
            intpart, frac = s, ""
        if not intpart.isdigit():
            # Not a plain number; return original unchanged for robustness.
            return value
        intpart = _comma_int(intpart)
        return f"{sign}{intpart}{frac}"

    # For numeric types or when rounding requested, use Decimal for stability.
    if ndigits is not None:
        try:
            d = Decimal(str(value))
        except Exception:
            return str(value)
        q = Decimal("1") if ndigits == 0 else Decimal("1").scaleb(-ndigits)
        # quantize rounds; use default rounding (banker's) like Decimal.
        try:
            d = d.quantize(q)
        except Exception:
            # Some values may not quantize cleanly; fall back to formatting.
            fmt = f"{{0:.{ndigits}f}}"
            try:
                s = fmt.format(float(value))
            except Exception:
                return str(value)
        else:
            s = format(d, "f")
        # Now comma-separate integer part.
        sign = ""
        if s.startswith(("-", "+")):
            sign = "-" if s[0] == "-" else ""
            s = s[1:]
        if "." in s:
            intpart, fracpart = s.split(".", 1)
            frac = "." + fracpart
        else:
            intpart, frac = s, ""
        if not intpart.isdigit():
            return str(value)
        return f"{sign}{_comma_int(intpart)}{frac}"

    # ndigits is None and value is not a string: create a fixed decimal string
    # where possible, then comma.
    decs = _to_decimal_str(value)
    if decs is None:
        return str(value)

    sign = ""
    s = decs
    if s.startswith(("-", "+")):
        sign = "-" if s[0] == "-" else ""
        s = s[1:]
    if "." in s:
        intpart, fracpart = s.split(".", 1)
        frac = "." + fracpart
    else:
        intpart, frac = s, ""
    if not intpart.isdigit():
        return str(value)
    return f"{sign}{_comma_int(intpart)}{frac}"


def _comma_int(digits: str) -> str:
    # digits is assumed to be only 0-9
    n = len(digits)
    if n <= 3:
        return digits
    parts = []
    i = n
    while i > 3:
        parts.append(digits[i - 3 : i])
        i -= 3
    parts.append(digits[:i])
    return ",".join(reversed(parts))


def ordinal(value: Any) -> str:
    """
    Convert an integer to its ordinal representation in English.
    """
    if value is None:
        raise TypeError("value must not be None")

    n: int
    if isinstance(value, bool):
        # bool is int subclass; treat explicitly for clarity
        n = int(value)
    elif isinstance(value, int):
        n = value
    elif isinstance(value, str):
        s = value.strip()
        if not s:
            raise ValueError("invalid literal for ordinal")
        try:
            n = int(s, 10)
        except ValueError:
            # Try float->int only if integral.
            try:
                f = float(s)
            except ValueError as e:
                raise ValueError("invalid literal for ordinal") from e
            if not f.is_integer():
                raise ValueError("invalid literal for ordinal")
            n = int(f)
    else:
        # Try int conversion; if fails, attempt float integral.
        try:
            n = int(value)
        except Exception:
            try:
                f = float(value)
            except Exception as e:
                raise ValueError("invalid literal for ordinal") from e
            if not f.is_integer():
                raise ValueError("invalid literal for ordinal")
            n = int(f)

    absn = abs(n)
    if 10 <= (absn % 100) <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(absn % 10, "th")
    return f"{n}{suf}"