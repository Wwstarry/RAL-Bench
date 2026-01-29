from __future__ import annotations

import decimal
import math
import re
from fractions import Fraction
from typing import Any, Iterable, Optional, Tuple

from .i18n import gettext, ngettext

_INT_RE = re.compile(r"^-?\d+$")


def _to_decimal(x: Any) -> decimal.Decimal:
    if isinstance(x, decimal.Decimal):
        return x
    if isinstance(x, (int,)):
        return decimal.Decimal(x)
    if isinstance(x, float):
        # Avoid binary float repr noise; str() matches reference behavior better.
        return decimal.Decimal(str(x))
    if isinstance(x, str):
        return decimal.Decimal(x)
    try:
        return decimal.Decimal(str(x))
    except Exception:
        return decimal.Decimal(0)


def intcomma(value: Any) -> str:
    """
    Convert an integer or float to a string containing commas as thousands separators.

    Compatible with humanize.intcomma for common cases.
    """
    if value is None:
        return "0"
    s = str(value)

    # Preserve scientific notation
    if "e" in s.lower():
        return s

    sign = ""
    if s.startswith("-"):
        sign, s = "-", s[1:]

    if "." in s:
        int_part, frac_part = s.split(".", 1)
        int_part_commas = "{:,}".format(int(int_part)) if int_part and _INT_RE.match(int_part) else _comma_str(int_part)
        return f"{sign}{int_part_commas}.{frac_part}"
    # integer-like
    if _INT_RE.match(s):
        return f"{sign}{int(s):,}"
    return f"{sign}{_comma_str(s)}"


def _comma_str(s: str) -> str:
    # Insert commas every 3 digits from the right, ignoring non-digits.
    # Used as a fallback for unusual inputs.
    digits = list(s)
    out = []
    count = 0
    for ch in reversed(digits):
        if ch.isdigit():
            if count and count % 3 == 0:
                out.append(",")
            count += 1
        out.append(ch)
    return "".join(reversed(out))


def ordinal(value: Any) -> str:
    """
    Convert an integer to its ordinal representation (1 -> 1st, 2 -> 2nd, ...).
    """
    try:
        n = int(value)
    except Exception:
        return str(value)
    suffix = "th"
    if 10 <= (n % 100) <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def apnumber(value: Any) -> str:
    """
    For numbers 1-9, return the number spelled out as a word. Otherwise return as string.
    """
    try:
        n = int(value)
    except Exception:
        return str(value)
    words = {
        1: gettext("one"),
        2: gettext("two"),
        3: gettext("three"),
        4: gettext("four"),
        5: gettext("five"),
        6: gettext("six"),
        7: gettext("seven"),
        8: gettext("eight"),
        9: gettext("nine"),
    }
    return words.get(n, str(n))


def fraction(value: Any, format: str = "fraction") -> str:
    """
    Render a float/decimal as a human fraction.
    `format` can be 'fraction' or 'ratio' (very small subset).
    """
    try:
        d = _to_decimal(value)
    except Exception:
        return str(value)

    # Convert to Fraction with limited denominator to avoid huge outputs.
    try:
        f = Fraction(d).limit_denominator(1000)
    except Exception:
        try:
            f = Fraction(float(d)).limit_denominator(1000)
        except Exception:
            return str(value)

    if format == "ratio":
        return f"{f.numerator}:{f.denominator}"
    # default
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def scientific(value: Any, precision: int = 2) -> str:
    try:
        x = float(value)
    except Exception:
        return str(value)
    if math.isnan(x) or math.isinf(x):
        return str(value)
    fmt = f"{{:.{precision}e}}"
    return fmt.format(x)


def metric(value: Any, precision: int = 1) -> str:
    """
    Format a number with metric (SI) prefixes: k, M, G, T, P, E.

    This is a minimal approximation, intended for compatibility in tests that
    expect the function to exist.
    """
    try:
        x = float(value)
    except Exception:
        return str(value)

    prefixes = [
        (1e18, "E"),
        (1e15, "P"),
        (1e12, "T"),
        (1e9, "G"),
        (1e6, "M"),
        (1e3, "k"),
    ]
    sign = "-" if x < 0 else ""
    x = abs(x)
    for factor, prefix in prefixes:
        if x >= factor:
            v = x / factor
            s = f"{v:.{precision}f}".rstrip("0").rstrip(".")
            return f"{sign}{s}{prefix}"
    s = f"{x:.{precision}f}".rstrip("0").rstrip(".")
    return f"{sign}{s}"


def intword(value: Any, format: str = "%.1f") -> str:
    """
    Convert large numbers to a human-readable format using words:
    thousand, million, billion, trillion, quadrillion.
    """
    try:
        x = float(value)
    except Exception:
        return str(value)

    sign = "-" if x < 0 else ""
    x = abs(x)
    if x < 1000:
        # keep as integer if it looks integral
        if float(int(x)) == x:
            return f"{sign}{int(x)}"
        return f"{sign}{x}"

    words: Tuple[Tuple[float, str], ...] = (
        (1e15, gettext("quadrillion")),
        (1e12, gettext("trillion")),
        (1e9, gettext("billion")),
        (1e6, gettext("million")),
        (1e3, gettext("thousand")),
    )
    for factor, word in words:
        if x >= factor:
            v = x / factor
            try:
                s = (format % v).rstrip("0").rstrip(".")
            except Exception:
                s = f"{v:.1f}".rstrip("0").rstrip(".")
            return f"{sign}{s} {word}"
    return f"{sign}{x}"


def _pluralize(word_singular: str, word_plural: str, n: int) -> str:
    return ngettext(word_singular, word_plural, n)