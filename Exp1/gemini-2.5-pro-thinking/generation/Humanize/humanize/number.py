import re
from fractions import Fraction
from .i18n import gettext as _, ngettext


def ordinal(value):
    """
    Converts an integer to its ordinal as a string. 1 is '1st', 2 is '2nd',
    3 is '3rd', etc. Works for any integer.
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValueError("must be an integer.")

    if value % 100 in (11, 12, 13):
        return f"{value}th"

    last_digit = value % 10
    if last_digit == 1:
        return f"{value}st"
    if last_digit == 2:
        return f"{value}nd"
    if last_digit == 3:
        return f"{value}rd"

    return f"{value}th"


def intcomma(value):
    """
    Converts an integer or float to a string containing commas every three
    digits.
    """
    try:
        if isinstance(value, str):
            if "." in value:
                float(value)
            else:
                int(value)
    except (TypeError, ValueError):
        return value

    orig = str(value)
    if "." in orig:
        integer_part, decimal_part = orig.split(".", 1)
    else:
        integer_part, decimal_part = orig, None

    if len(integer_part) <= 3:
        return orig

    integer_part = re.sub(r"(\d)(?=(\d{3})+$)", r"\1,", integer_part)

    if decimal_part:
        return integer_part + "." + decimal_part
    else:
        return integer_part


def intword(value, format="%.1f"):
    """
    Converts a large integer to a friendly text representation.
    Works best for numbers over 1 million. For example,
    1000000 becomes '1.0 million', 1200000 becomes '1.2 million' and
    '1200000000' becomes '1.2 billion'.
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value

    if value < 1000000:
        return str(value)

    powers = [
        (10**12, _("trillion")),
        (10**9, _("billion")),
        (10**6, _("million")),
    ]

    for power, name in powers:
        if value >= power:
            return (format + " %s") % (value / power, name)

    return str(value)


def apnumber(value):
    """
    For numbers 1-9, returns the number spelled out. Otherwise, returns the
    number as a string.
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value

    if not 0 < value < 10:
        return str(value)

    words = [
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
    return words[value - 1]


def fractional(value):
    """
    Converts a float to a fractional representation.
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value

    f = Fraction(value).limit_denominator()

    if f.denominator == 1:
        return str(f.numerator)

    integer_part = f.numerator // f.denominator
    fraction_part = f - integer_part

    parts = []
    if integer_part > 0:
        parts.append(str(integer_part))

    vulgar_fractions = {
        (1, 2): "½", (1, 3): "⅓", (2, 3): "⅔",
        (1, 4): "¼", (3, 4): "¾", (1, 5): "⅕",
        (2, 5): "⅖", (3, 5): "⅗", (4, 5): "⅘",
        (1, 6): "⅙", (5, 6): "⅚", (1, 8): "⅛",
        (3, 8): "⅜", (5, 8): "⅝", (7, 8): "⅞",
    }

    key = (fraction_part.numerator, fraction_part.denominator)
    if key in vulgar_fractions:
        parts.append(vulgar_fractions[key])
    else:
        parts.append(f"{fraction_part.numerator}/{fraction_part.denominator}")

    return " ".join(parts)


def scientific(value, precision=2):
    """
    Formats a number in scientific notation.
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value

    return f"{value:.{precision}e}"