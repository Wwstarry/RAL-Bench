import math

def intcomma(value):
    """
    Converts an integer to a string containing commas every three digits.
    """
    try:
        orig = value
        if isinstance(value, float):
            value = int(value)
        s = str(abs(int(value)))
    except Exception:
        return str(value)
    if len(s) <= 3:
        result = s
    else:
        groups = []
        while s:
            groups.append(s[-3:])
            s = s[:-3]
        result = ",".join(reversed(groups))
    if int(orig) < 0:
        result = "-" + result
    if isinstance(orig, float):
        # preserve decimal part
        dec = str(orig).partition(".")[2]
        if dec and int(dec) != 0:
            result += "." + dec
    return result

def ordinal(value):
    """
    Converts an integer to its ordinal as a string.
    """
    try:
        value = int(value)
    except Exception:
        return str(value)
    suffix = "th"
    if value % 100 not in (11, 12, 13):
        if value % 10 == 1:
            suffix = "st"
        elif value % 10 == 2:
            suffix = "nd"
        elif value % 10 == 3:
            suffix = "rd"
    return f"{value}{suffix}"