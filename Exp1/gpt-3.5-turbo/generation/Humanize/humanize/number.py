def intcomma(value):
    """
    Convert an integer to a string containing commas every three digits.
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    s = str(value)
    if len(s) <= 3:
        return s
    # Insert commas every three digits from the right
    parts = []
    while s and s[-1].isdigit():
        parts.append(s[-3:])
        s = s[:-3]
    parts.reverse()
    return ','.join(parts)


def ordinal(value):
    """
    Convert an integer to its ordinal as a string.
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    suffix = "th"
    if 10 <= (value % 100) <= 20:
        suffix = "th"
    else:
        if value % 10 == 1:
            suffix = "st"
        elif value % 10 == 2:
            suffix = "nd"
        elif value % 10 == 3:
            suffix = "rd"
    return f"{value}{suffix}"