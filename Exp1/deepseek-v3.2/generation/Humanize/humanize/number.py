"""
Number humanization utilities.
"""

import math
import re
from typing import Union, Optional

from humanize.i18n import gettext as _, ngettext, thousands_separator, decimal_separator

def intcomma(value: Union[int, float, str], ndigits: Optional[int] = None) -> str:
    """
    Convert an integer or float to a string with commas.

    Args:
        value: The number to format.
        ndigits: If provided, round to this many decimal places.

    Returns:
        Formatted string with thousands separators.
    """
    if ndigits is not None:
        try:
            value = round(float(value), ndigits)
        except (TypeError, ValueError):
            pass

    if isinstance(value, (int, float)):
        # Format with proper decimal separator
        if isinstance(value, int):
            s = str(value)
            decimal_part = ""
        else:
            s = str(value)
            if "." in s:
                int_part, decimal_part = s.split(".", 1)
                decimal_part = decimal_separator() + decimal_part
            else:
                int_part = s
                decimal_part = ""

        # Add thousands separators
        sep = thousands_separator()
        if sep:
            # Add separators every 3 digits from the right
            int_part = re.sub(r"(\d)(?=(\d{3})+(?!\d))", r"\1" + sep, int_part[::-1])[::-1]

        return int_part + decimal_part
    else:
        # For string values, try to parse as number
        try:
            return intcomma(float(value), ndigits)
        except (TypeError, ValueError):
            return str(value)

def intword(value: Union[int, float, str], format: str = "%.1f") -> str:
    """
    Convert a large integer to a friendly text representation.

    Args:
        value: The number to format.
        format: Format string for the number part.

    Returns:
        Human-readable string like "1.2 million".
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)

    if value < 1000:
        return str(int(value))

    powers = [
        (10**12, _("trillion")),
        (10**9, _("billion")),
        (10**6, _("million")),
        (10**3, _("thousand")),
    ]

    for power, word in powers:
        if value >= power:
            scaled = value / power
            return (format % scaled).rstrip("0").rstrip(".") + " " + word

    return str(int(value))

def apnumber(value: Union[int, float, str]) -> str:
    """
    Convert an integer to Associated Press style.

    For numbers 0-9, returns the word form. For 10+, returns the numeral.

    Args:
        value: The number to format.

    Returns:
        Word form for 0-9, numeral string otherwise.
    """
    try:
        num = int(float(value))
    except (TypeError, ValueError):
        return str(value)

    ap_numbers = [
        _("zero"),
        _("one"),
        _("two"),
        _("three"),
        _("four"),
        _("five"),
        _("six"),
        _("seven"),
        _("eight"),
        _("nine"),
    ]

    if 0 <= num <= 9:
        return ap_numbers[num]
    else:
        return str(num)

def fractional(value: Union[int, float, str]) -> str:
    """
    Convert a float to a fraction.

    Args:
        value: The number to convert.

    Returns:
        Fraction string like "1 1/2".
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)

    if value == 0:
        return "0"

    whole = int(value)
    fraction = abs(value - whole)

    if fraction == 0:
        return str(whole)

    # Common fractions
    common_fractions = [
        (0.5, "1/2"),
        (0.3333, "1/3"),
        (0.6667, "2/3"),
        (0.25, "1/4"),
        (0.75, "3/4"),
        (0.2, "1/5"),
        (0.4, "2/5"),
        (0.6, "3/5"),
        (0.8, "4/5"),
        (0.1667, "1/6"),
        (0.8333, "5/6"),
        (0.125, "1/8"),
        (0.375, "3/8"),
        (0.625, "5/8"),
        (0.875, "7/8"),
    ]

    for frac_value, frac_str in common_fractions:
        if abs(fraction - frac_value) < 0.01:
            if whole == 0:
                return frac_str
            elif value < 0:
                return f"-{abs(whole)} {frac_str}"
            else:
                return f"{whole} {frac_str}"

    # Fallback to decimal
    return str(value)

def scientific(value: Union[int, float, str], precision: int = 2) -> str:
    """
    Convert a number to scientific notation.

    Args:
        value: The number to format.
        precision: Number of decimal places.

    Returns:
        Scientific notation string.
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)

    if value == 0:
        return "0"

    exp = int(math.floor(math.log10(abs(value))))
    coeff = value / (10**exp)

    coeff_str = f"{coeff:.{precision}f}".rstrip("0").rstrip(".")
    return f"{coeff_str}×10^{exp}"

def ordinal(value: Union[int, float, str]) -> str:
    """
    Convert an integer to its ordinal as a string.

    Args:
        value: The number to convert.

    Returns:
        Ordinal string like "1st", "2nd", etc.
    """
    try:
        num = int(float(value))
    except (TypeError, ValueError):
        return str(value)

    if 10 <= num % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(num % 10, "th")

    return str(num) + suffix

def clamp(value: Union[int, float, str], min: float, max: float) -> Union[int, float, str]:
    """
    Clamp a value between minimum and maximum bounds.

    Args:
        value: The value to clamp.
        min: Minimum bound.
        max: Maximum bound.

    Returns:
        Clamped value.
    """
    try:
        num = float(value)
    except (TypeError, ValueError):
        return value

    if num < min:
        return min
    elif num > max:
        return max
    else:
        # Return as int if it's an integer
        if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
            return int(num)
        return num