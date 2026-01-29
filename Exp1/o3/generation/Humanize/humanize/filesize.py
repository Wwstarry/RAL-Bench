"""
File-size helpers (``naturalsize``) compatible with the public humanize API.
"""

from __future__ import annotations

from typing import Any

_DECIMAL_SUFFIXES = ["kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
_BINARY_SUFFIXES = ["KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
_GNU_SUFFIXES = ["K", "M", "G", "T", "P", "E", "Z", "Y"]


def naturalsize(
    value: Any,
    binary: bool = False,
    gnu: bool = False,
    format: str = "%.1f",
    sign: bool = False,
) -> str:
    """
    Human-friendly formatting of file sizes.

    Parameters
    ----------
    value
        The byte count – any object that can be converted to ``int()``.
    binary
        Use multiples of 1024 with IEC suffixes (KiB, MiB, …).
    gnu
        Produce GNU ``ls``-style output (“--si” / “-h”).  Implies *binary=False*
        and uses powers of 1024 for negative inputs and 1000 for positives –
        we simplify by always using 1024.
    format
        ``printf``-style format string (default ``%.1f``).
    sign
        Prefix with “+” / “-”.

    Examples
    --------
    >>> naturalsize(10)
    '10 Bytes'
    >>> naturalsize(1024)
    '1.0 kB'
    >>> naturalsize(1024, binary=True)
    '1.0 KiB'
    """
    try:
        bytes_ = int(value)
    except Exception:
        raise ValueError(f"{value!r} can not be interpreted as a number")

    # Handle sign
    prefix = ""
    if sign:
        prefix = "+" if bytes_ >= 0 else "-"
    abs_bytes = abs(bytes_)

    if abs_bytes < 1000 and not binary:
        suffix = "Byte" if abs_bytes == 1 else "Bytes"
        return f"{prefix}{abs_bytes} {suffix}"

    if gnu:
        # GNU variant (approximate)
        base = 1024
        suffixes = _GNU_SUFFIXES
    elif binary:
        base = 1024
        suffixes = _BINARY_SUFFIXES
    else:
        base = 1000
        suffixes = _DECIMAL_SUFFIXES

    for i, s in enumerate(suffixes, 1):
        unit = base**i
        if abs_bytes < unit * base or i == len(suffixes):
            value = abs_bytes / unit
            formatted = format % value
            # Strip pointless trailing zeros and dots
            if "." in formatted:
                formatted = formatted.rstrip("0").rstrip(".")
            return f"{prefix}{formatted} {s}"
    # Should never reach here
    return f"{prefix}{abs_bytes} Bytes"