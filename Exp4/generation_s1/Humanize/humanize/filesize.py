from __future__ import annotations

from typing import Any, List, Tuple


_DECIMAL_UNITS: List[str] = ["B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
_BINARY_UNITS: List[str] = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
_GNU_UNITS: List[str] = ["B", "K", "M", "G", "T", "P", "E", "Z", "Y"]


def naturalsize(
    value: Any,
    binary: bool = False,
    format: str = "%.1f",
    suffix: str = "B",
    GNU: bool = False,
) -> str:
    """
    Format a byte count as a human-readable size.

    Defaults aim to be compatible with commonly used humanize behaviors:
    - decimal by default (1000-based): 1 kB, 1 MB, ...
    - binary=True uses IEC: 1 KiB, 1 MiB, ...
    - GNU=True uses GNU style: 1K, 1M, ... and bytes as 512B
    """
    if value is None:
        raise ValueError("naturalsize() requires a value")

    try:
        n = float(value)
    except Exception as e:
        raise ValueError("naturalsize() requires a numeric value") from e

    sign = "-" if n < 0 else ""
    n = abs(n)

    if GNU:
        base = 1024.0 if binary else 1000.0
        units = _GNU_UNITS
        # GNU style usually no space; "B" appended for bytes, and no extra suffix.
        if n < base:
            # Preserve integer if possible
            return f"{sign}{_format_number(n, '%.0f')}{units[0]}"
        scaled, unit = _scale(n, base, units)
        num = _format_number(scaled, format)
        # Do not append suffix for K/M/G etc; unit already represents it.
        return f"{sign}{num}{unit}"

    base = 1024.0 if binary else 1000.0
    units = _BINARY_UNITS if binary else _DECIMAL_UNITS

    if n == 0:
        return f"{sign}0 {units[0]}" if units[0] else f"{sign}0"

    scaled, unit = _scale(n, base, units)
    num = _format_number(scaled, format)

    # If caller overrides suffix, replace final "B" notion.
    # Reference humanize keeps unit text; here we keep unit and allow suffix param
    # mainly for compatibility.
    if suffix != "B":
        if unit.endswith("B"):
            unit = unit[:-1] + suffix
        elif unit == "B":
            unit = suffix

    return f"{sign}{num} {unit}"


def _scale(n: float, base: float, units: List[str]) -> Tuple[float, str]:
    idx = 0
    max_idx = len(units) - 1
    while n >= base and idx < max_idx:
        n /= base
        idx += 1
    return n, units[idx]


def _format_number(n: float, fmt: str) -> str:
    s = fmt % n
    # Normalize common cases: drop trailing ".0"
    if "." in s:
        s2 = s.rstrip("0").rstrip(".")
        if s2:
            s = s2
    return s