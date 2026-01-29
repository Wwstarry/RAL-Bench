"""
Number formatting utilities compatible with core 'humanize' expectations.
"""

from decimal import Decimal, InvalidOperation


def _to_str_number(value):
    """
    Convert value to a string representing a number without scientific notation when possible.
    """
    if isinstance(value, (int,)):
        return str(value)
    if isinstance(value, float):
        # Use repr to avoid locale, but convert scientific notation to plain if possible
        s = format(value, "f")
        # Trim trailing zeros in fractional part but preserve at least one digit if decimal exists
        if "." in s:
            s = s.rstrip("0").rstrip(".") if s.rstrip("0").rstrip(".") != "" else "0"
        return s
    if isinstance(value, Decimal):
        s = format(value, "f")
        return s
    # fallback: string input
    s = str(value)
    # Attempt to normalize if Decimal can parse it.
    try:
        d = Decimal(s)
        # Keep scale if original had decimal point
        s2 = format(d, "f")
        return s2
    except (InvalidOperation, ValueError):
        return s


def intcomma(value, sep=",", decimal_sep="."):
    """
    Format an integer or the integer part of a number with a thousands separator.

    Examples:
    - intcomma(1000) -> '1,000'
    - intcomma(12345.67) -> '12,345.67'
    - intcomma(-1234567) -> '-1,234,567'
    """
    s = _to_str_number(value)
    # Handle sign
    sign = ""
    if s.startswith(("+", "-")):
        sign = s[0]
        s = s[1:]

    # Split decimal part
    if decimal_sep in s:
        int_part, dec_part = s.split(decimal_sep, 1)
        dec = decimal_sep + dec_part
    elif "." in s and decimal_sep != ".":
        # normalize '.' to decimal_sep if needed
        int_part, dec_part = s.split(".", 1)
        dec = decimal_sep + dec_part
    else:
        int_part, dec = s, ""

    # Group integer part
    # Remove any pre-existing separators for safety
    int_part = int_part.replace(sep, "").replace("_", "")
    # If int_part is not numeric (e.g. 'nan'), return original string
    if not int_part or any(ch not in "0123456789" for ch in int_part):
        return sign + s

    # Insert grouping from the right
    n = len(int_part)
    groups = []
    while n > 3:
        groups.append(int_part[n - 3 : n])
        n -= 3
    if n > 0:
        groups.append(int_part[0:n])
    grouped = sep.join(reversed(groups))
    return f"{sign}{grouped}{dec}"


def ordinal(value):
    """
    Convert an integer to its ordinal as a string:

    1 -> '1st', 2 -> '2nd', 3 -> '3rd', 4 -> '4th', 11 -> '11th'
    """
    try:
        n = int(value)
    except Exception:
        # If not convertible, return original as string
        return str(value)

    abs_n = abs(n)
    # Special case for 11, 12, 13
    if 10 <= (abs_n % 100) <= 13:
        suffix = "th"
    else:
        last = abs_n % 10
        if last == 1:
            suffix = "st"
        elif last == 2:
            suffix = "nd"
        elif last == 3:
            suffix = "rd"
        else:
            suffix = "th"
    return f"{n}{suffix}"