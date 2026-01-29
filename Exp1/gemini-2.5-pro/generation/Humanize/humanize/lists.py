"""Human-readable lists."""

from .i18n import gettext as _


def humanize_list(items, conjunction="and"):
    """
    Joins a list of strings into a human-readable, comma-separated string.
    """
    items = [str(item) for item in items]
    count = len(items)
    if count == 0:
        return ""
    if count == 1:
        return items[0]
    if count == 2:
        return _("%s %s %s") % (items[0], conjunction, items[1])

    # More than 2 items: "item1, item2, and item3"
    head = ", ".join(items[:-1])
    return _("%s, %s %s") % (head, conjunction, items[-1])