"""
List humanization helpers.
"""


def natural_list(items, conjunction="and", serial_comma=True):
    """
    Join a list of items with commas and a conjunction, optionally using the serial (Oxford) comma.

    Examples:
    - natural_list(['apples']) -> 'apples'
    - natural_list(['apples', 'bananas']) -> 'apples and bananas'
    - natural_list(['apples', 'bananas', 'cherries']) -> 'apples, bananas, and cherries'
    - natural_list(['apples', 'bananas', 'cherries'], serial_comma=False) -> 'apples, bananas and cherries'
    """
    items = list(items)
    n = len(items)
    if n == 0:
        return ""
    if n == 1:
        return str(items[0])
    if n == 2:
        return f"{items[0]} {conjunction} {items[1]}"

    middle = ", ".join(str(x) for x in items[:-1])
    last = str(items[-1])
    comma = "," if serial_comma else ""
    return f"{middle}{comma} {conjunction} {last}"