"""
File size humanization utilities.
"""

import math
from typing import Union

from humanize.i18n import gettext as _, ngettext

def naturalsize(
    value: Union[int, float],
    binary: bool = False,
    gnu: bool = False,
    format: str = "%.1f",
) -> str:
    """
    Return a human-readable representation of a file size.

    Args:
        value: Size in bytes.
        binary: If True, use binary prefixes (KiB, MiB, etc.).
        gnu: If True, use GNU style (K, M, etc. for binary).
        format: Format string for the number part.

    Returns:
        Human-readable size.
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)

    if value < 0:
        return str(value)

    if value == 0:
        return _("0 bytes")

    if binary:
        base = 1024
        prefixes = ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi", "Yi"]
        if gnu:
            suffixes = ["B", "K", "M", "G", "T", "P", "E", "Z", "Y"]
        else:
            suffixes = ["B"] + [p + "B" for p in prefixes[1:]]
    else:
        base = 1000
        prefixes = ["", "k", "M", "G", "T", "P", "E", "Z", "Y"]
        suffixes = ["B"] + [p + "B" for p in prefixes[1:]]

    # Determine appropriate unit
    if value < base:
        unit = 0
    else:
        unit = int(math.floor(math.log(value, base)))
        unit = min(unit, len(suffixes) - 1)

    # Format the number
    scaled = value / (base**unit)
    if unit == 0:
        # For bytes, use integer
        return ngettext("%d byte", "%d bytes", int(value)) % value
    else:
        number_str = (format % scaled).rstrip("0").rstrip(".")
        return f"{number_str} {suffixes[unit]}"