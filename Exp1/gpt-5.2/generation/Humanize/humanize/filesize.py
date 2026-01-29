from __future__ import annotations

from typing import Any, Iterable, Tuple

from .i18n import gettext


_DECIMAL_SUFFIXES: Tuple[str, ...] = ("B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
_BINARY_SUFFIXES: Tuple[str, ...] = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")


def naturalsize(
    value: Any,
    binary: bool = False,
    format: str = "%.1f",
    suffix: str = "",
    always: bool = False,
) -> str:
    """
    Format a byte count as a human readable file size.

    Parameters mimic the reference library for common usage:
    - binary: use powers of 1024 and IEC suffixes (KiB, MiB, ...)
    - format: sprintf-style format applied to the scaled value
    - suffix: appended after the unit (often 'B' or '/s'); kept for compatibility
    - always: always show a decimal point even for bytes
    """
    try:
        n = float(value)
    except Exception:
        return str(value)

    if n < 0:
        sign = "-"
        n = -n
    else:
        sign = ""

    base = 1024.0 if binary else 1000.0
    suffixes = _BINARY_SUFFIXES if binary else _DECIMAL_SUFFIXES

    # Bytes special-case
    if n < base:
        if always and n != 1:
            # e.g. "0.0 B" or "12.0 B"
            try:
                s = (format % n).rstrip("0").rstrip(".")
            except Exception:
                s = str(int(n))
            # If user wants always, keep one decimal
            if "." not in (format % n):
                s = f"{n:.1f}"
        else:
            s = str(int(n)) if float(int(n)) == n else str(n)
        unit = suffixes[0]
        return f"{sign}{s} {unit}{suffix}".rstrip()

    i = 0
    while n >= base and i < len(suffixes) - 1:
        n /= base
        i += 1

    try:
        s = (format % n).rstrip("0").rstrip(".")
    except Exception:
        s = f"{n:.1f}".rstrip("0").rstrip(".")
    unit = suffixes[i]
    return f"{sign}{s} {unit}{suffix}".rstrip()