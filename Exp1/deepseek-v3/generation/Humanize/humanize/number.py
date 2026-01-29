def intcomma(value):
    """Convert an integer to a string containing commas every three digits."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"intcomma() argument must be int or float, not {type(value).__name__}")
    return "{:,}".format(value)

def ordinal(value):
    """Convert an integer to its ordinal as a string."""
    if not isinstance(value, int):
        raise TypeError(f"ordinal() argument must be int, not {type(value).__name__}")
    
    if value % 100 in (11, 12, 13):
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
    return f"{value}{suffix}"