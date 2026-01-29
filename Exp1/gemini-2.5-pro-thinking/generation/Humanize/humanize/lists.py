from .i18n import gettext as _


def naturalist(items, sep=", ", conj=None):
    """Joins a list of strings into a natural language phrase."""
    if conj is None:
        conj = " " + _("and") + " "

    items = [str(item) for item in items]
    count = len(items)

    if count == 0:
        return ""
    if count == 1:
        return items[0]
    if count == 2:
        return items[0] + conj + items[1]

    return sep.join(items[:-1]) + conj + items[-1]


def oxford(items, sep=", ", conj=None):
    """Joins a list of strings with an Oxford comma."""
    if conj is None:
        conj = " " + _("and") + " "

    items = [str(item) for item in items]
    count = len(items)

    if count == 0:
        return ""
    if count == 1:
        return items[0]
    if count == 2:
        return items[0] + conj + items[1]

    return sep.join(items[:-1]) + "," + conj + items[-1]