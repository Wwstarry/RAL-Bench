"""Human-readable numbers."""

from .i18n import gettext as _


def intcomma(value, ndigits=None):
    """
    Converts an integer or float to a string containing commas every three digits.

    For example, 3000 becomes '3,000' and 45000.99 becomes '45,000.99'.
    """
    try:
        if ndigits is not None:
            s = f"{value:.{ndigits}f}"
        else:
            s = str(value)
    except (TypeError, ValueError):
        return str(value)

    if "." in s:
        integer_part, decimal_part = s.split(".", 1)
    else:
        integer_part, decimal_part = s, None

    sign = ""
    if integer_part.startswith("-"):
        sign = "-"
        integer_part = integer_part[1:]

    if len(integer_part) > 3:
        rev = integer_part[::-1]
        parts = [rev[i : i + 3] for i in range(0, len(rev), 3)]
        integer_part_with_commas = ",".join(parts)[::-1]
    else:
        integer_part_with_commas = integer_part

    result = sign + integer_part_with_commas
    if decimal_part is not None:
        result += "." + decimal_part

    return result


def ordinal(value):
    """
    Converts an integer to its ordinal as a string.

    For example, 1 becomes '1st', 2 becomes '2nd', 3 becomes '3rd', etc.
    Works for any integer.
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return str(value)

    # Special cases for 11, 12, 13
    if value % 100 in (11, 12, 13):
        suffix = "th"
    else:
        last_digit = value % 10
        if last_digit == 1:
            suffix = "st"
        elif last_digit == 2:
            suffix = "nd"
        elif last_digit == 3:
            suffix = "rd"
        else:
            suffix = "th"

    return str(value) + suffix