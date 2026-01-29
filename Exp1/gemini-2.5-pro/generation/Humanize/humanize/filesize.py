"""Human-readable file sizes."""

from .i18n import gettext as _, ngettext


def naturalsize(value, binary=False, gnu=False, format="%.1f"):
    """
    Format a number of bytes in a human-readable format.
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return str(value)

    if gnu:
        binary = True

    if binary:
        base = 1024
        if gnu:
            suffixes = ["", "K", "M", "G", "T", "P", "E", "Z", "Y"]
        else:
            suffixes = [" B", " KiB", " MiB", " GiB", " TiB", " PiB", " EiB", " ZiB", " YiB"]
    else:
        base = 1000
        suffixes = [" B", " KB", " MB", " GB", " TB", " PB", " EB", " ZB", " YB"]

    if value == 0:
        return "0" if gnu else "0" + suffixes[0]

    sign = "-" if value < 0 else ""
    value = abs(value)

    for i, suffix in enumerate(suffixes):
        unit = base**i
        if value < unit * base or i == len(suffixes) - 1:
            if i == 0:
                num_str = str(value)
                current_suffix = "" if gnu else suffix
            else:
                num = value / unit
                if gnu:
                    if num < 10:
                        num_str = "%.1f" % num
                        if num_str.endswith(".0"):
                            num_str = num_str[:-2]
                    else:
                        num_str = str(int(round(num)))
                else:
                    num_str = format % num
                current_suffix = suffix

            if gnu:
                return f"{sign}{num_str}{current_suffix}"
            else:
                return f"{sign}{num_str}{current_suffix}"

    # Fallback, should not be reached
    return str(value)