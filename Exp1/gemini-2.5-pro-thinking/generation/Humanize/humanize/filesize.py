from .i18n import gettext as _, ngettext


def naturalsize(value, binary=False, gnu=False, format="%.1f"):
    """Format a number of bytes in a human-readable format."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value

    if gnu:
        binary = True

    if binary:
        base = 1024
        if gnu:
            suffixes = ["B", "K", "M", "G", "T", "P", "E", "Z", "Y"]
        else:
            suffixes = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
    else:
        base = 1000
        suffixes = ["B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]

    if value < 0:
        return "-" + naturalsize(-value, binary, gnu, format)

    if not gnu:
        if value == 1:
            return _("1 byte")
        if value < base:
            return ngettext("%d byte", "%d bytes", value) % value

    if value == 0:
        return "0 " + suffixes[0]

    for i, suffix in enumerate(suffixes):
        unit = base ** i
        if value < unit * base:
            if gnu:
                if i == 0:
                    return f"{value}{suffix}"
                # GNU style uses no space and removes trailing zeros
                num_str = (format % (value / unit)).rstrip("0").rstrip(".")
                return f"{num_str}{suffix}"
            else:
                return (format + " %s") % (value / unit, suffix)

    # Handle extremely large numbers
    i = len(suffixes) - 1
    unit = base ** i
    if gnu:
        num_str = (format % (value / unit)).rstrip("0").rstrip(".")
        return f"{num_str}{suffixes[-1]}"
    else:
        return (format + " %s") % (value / unit, suffixes[-1])