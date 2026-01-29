def intcomma(value):
    """
    Convert an integer to a string containing commas every three digits.
    Example: 1234567 -> '1,234,567'
    """
    if not isinstance(value, (int, float)):
        raise ValueError("intcomma expects an integer or float value.")
    return f"{value:,}"


def ordinal(value):
    """
    Convert an integer to its ordinal representation.
    Example: 1 -> '1st', 2 -> '2nd', 3 -> '3rd', etc.
    """
    if not isinstance(value, int):
        raise ValueError("ordinal expects an integer value.")
    suffix = ["th", "st", "nd", "rd"] + ["th"] * 6
    if 10 <= value % 100 <= 20:
        suffix_index = 0
    else:
        suffix_index = min(value % 10, 4)
    return f"{value}{suffix[suffix_index]}"