from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence, Tuple

from .number import _format_number, _to_number


# Common unit sets in humanize-like APIs
_DECIMAL_SUFFIXES = ("B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
_BINARY_SUFFIXES = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")


def naturalsize(
    value: Any,
    binary: bool = False,
    format: str = "%.1f",
    locale: str | None = None,  # accepted for compatibility
    *,  # keyword-only (matches many versions)
    gnu: bool = False,
) -> str:
    """
    Format a bytes value as a human-readable size.

    Parameters
    - value: bytes (int/float/str)
    - binary: base 1024 (KiB, MiB) if True, else base 1000 (kB, MB)
    - format: printf-style format for the mantissa (default '%.1f')
    - gnu: if True use GNU style:
        * base 1024
        * suffixes: K, M, G, T, P, E, Z, Y (with 'B' for bytes)
        * bytes shown as 'B' (not '1B' for 1)
    """
    n = _to_number(value)
    if n is None:
        return str(value)
    try:
        n_float = float(n)
    except Exception:
        return str(value)

    # Preserve sign; scale absolute value.
    sign = "-" if n_float < 0 else ""
    n_abs = abs(n_float)

    if gnu:
        # GNU style is binary with single-letter suffixes.
        base = 1024.0
        if n_abs < base:
            # For bytes, GNU tends to return "123B"
            return f"{sign}{int(n_abs)}B"
        suffixes = ("K", "M", "G", "T", "P", "E", "Z", "Y")
        i = 0
        v = n_abs
        while v >= base and i < len(suffixes) - 1:
            v /= base
            i += 1
        # For GNU, no 'iB', just letter; often no space.
        # Use provided format for mantissa.
        try:
            mantissa = (format % v).rstrip("0").rstrip(".")
        except Exception:
            # Fallback to a sane default
            mantissa = _format_number(v, 1)
        return f"{sign}{mantissa}{suffixes[i-1]}" if i > 0 else f"{sign}{int(n_abs)}B"

    base = 1024.0 if binary else 1000.0
    suffixes = _BINARY_SUFFIXES if binary else _DECIMAL_SUFFIXES

    if n_abs < base:
        return f"{sign}{int(n_abs)} {suffixes[0]}"

    i = 0
    v = n_abs
    while v >= base and i < len(suffixes) - 1:
        v /= base
        i += 1

    try:
        mantissa = format % v
    except Exception:
        # If given a format like "%.1f", mimic it.
        mantissa = _format_number(v, 1)

    # Common expectation: strip trailing zeros for formats that allow it.
    if "." in mantissa:
        mantissa = mantissa.rstrip("0").rstrip(".")

    return f"{sign}{mantissa} {suffixes[i]}"