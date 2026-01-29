"""
number.py

Human-readable number formatting utilities.
"""

import math

def intcomma(value, sep=","):
    """
    Convert an integer or float to a string containing commas every three digits in
    the integer portion. For example, 3000 becomes "3,000" and 4500.2 becomes
    "4,500.2".
    """
    try:
        val_str = str(value)
    except:
        return value

    if '.' in val_str:
        int_part, frac_part = val_str.split('.', 1)
    else:
        int_part, frac_part = val_str, None

    # Check for sign
    sign = ''
    if int_part.startswith('-'):
        sign = '-'
        int_part = int_part[1:]

    # Reverse the integer part for easier grouping from right to left
    rev = int_part[::-1]
    grouped = []
    for i in range(0, len(rev), 3):
        grouped.append(rev[i:i+3])
    int_part = sep.join(grouped)[::-1]
    output = sign + int_part

    if frac_part is not None:
        output += '.' + frac_part

    return output


def ordinal(value):
    """
    Convert an integer into its ordinal representation::
       1 -> 1st
       2 -> 2nd
       3 -> 3rd
       4 -> 4th
       ...
    """
    try:
        value = int(value)
    except:
        return value

    suffix = "th"
    if value % 100 not in (11, 12, 13):
        if value % 10 == 1:
            suffix = "st"
        elif value % 10 == 2:
            suffix = "nd"
        elif value % 10 == 3:
            suffix = "rd"
    return f"{value}{suffix}"


def intword(value, format="%.1f"):
    """
    Convert a large integer to a friendly text representation. Works best for
    numbers over 1 million. For example, 1000000 becomes '1.0 million'.
    """
    try:
        number = float(value)
    except:
        return str(value)

    abs_number = abs(number)
    if abs_number < 1000:
        return str(value)

    # Large number suffixes
    units = [
       (1e12, 'trillion'),
       (1e9, 'billion'),
       (1e6, 'million'),
       (1e3, 'thousand'),
    ]

    for cutoff, label in units:
        if abs_number >= cutoff:
            _new_val = number / cutoff
            return (format % _new_val) + ' ' + label

    return str(value)


def fractional(value, denominator=10):
    """
    Attempts to show a number as a mixed fraction. For example,
    if value=1.25, fractional=1 1/4
    """
    try:
        value_f = float(value)
    except:
        return str(value)

    whole = int(value_f)
    frac = abs(value_f - whole)

    frac_as_int = round(frac * denominator)
    if frac_as_int == 0:
        return str(whole)
    if frac_as_int == denominator:
        # e.g. 1.9998 ~ 2
        return str(whole + 1)

    return f"{whole} {frac_as_int}/{denominator}"


def apnumber(value):
    """
    Returns the number spelled out in AP style. Only for 1-9.
    1 -> one
    2 -> two
    ...
    9 -> nine
    otherwise returns the original number as a string.
    """
    ap_map = {
        0: "zero",
        1: "one",
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
        7: "seven",
        8: "eight",
        9: "nine"
    }
    try:
        value_i = int(value)
        if 0 <= value_i <= 9:
            return ap_map[value_i]
    except:
        pass
    return str(value)


def scientific_notation(value, precision=2):
    """
    Convert a number to scientific notation string with given precision. E.g.
    123456 -> '1.23e+05'
    """
    try:
        fmt_str = "{:." + str(precision) + "e}"
        return fmt_str.format(float(value))
    except:
        return str(value)