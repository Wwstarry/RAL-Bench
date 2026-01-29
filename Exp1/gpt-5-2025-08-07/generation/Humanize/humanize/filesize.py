"""
File size humanization helpers.
"""

from typing import Optional


# Powers of 1000 for decimal; powers of 1024 for binary
_DECIMAL_UNITS = ["Byte", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
_BINARY_UNITS = ["Byte", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]


def naturalsize(value, binary: bool = False, gnu: bool = False, format: str = "%.1f") -> Optional[str]:
    """
    Human-readable file size.

    - value: number of bytes (int, float)
    - binary: if True, use binary prefixes (KiB=1024, MiB, ...)
              if False, use decimal (kB=1000, MB, ...)
    - gnu: if True, return compact GNU-style suffixes without space (K, M, G... or Ki, Mi if binary)
    - format: format string applied to the scaled number for units above bytes (default '%.1f')

    Examples:
    - naturalsize(1) -> '1 Byte'
    - naturalsize(10) -> '10 Bytes'
    - naturalsize(1000) -> '1.0 kB'
    - naturalsize(1024, binary=True) -> '1.0 KiB'
    - naturalsize(1024, gnu=True) -> '1K'
    """
    if value is None:
        return None

    try:
        num = float(value)
    except Exception:
        # Not a number; return as string
        return str(value)

    if num != num:  # NaN
        return str(value)

    negative = num < 0
    num = abs(num)

    if binary:
        step = 1024.0
        units = _BINARY_UNITS
        gnu_suffixes = ["B", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi", "Yi"]
    else:
        step = 1000.0
        units = _DECIMAL_UNITS
        gnu_suffixes = ["B", "K", "M", "G", "T", "P", "E", "Z", "Y"]

    prefix = "-" if negative else ""

    # Bytes (0-1023 or 0-999)
    if num < step:
        # Use pluralization for bytes
        b = int(num)
        unit = "Byte" if b == 1 else "Bytes"
        return f"{prefix}{b} {unit}"

    # Scale up
    idx = 0
    value = num
    while value >= step and idx < len(units) - 1:
        value /= step
        idx += 1

    if gnu:
        # GNU style drops the space and uses compact suffixes
        # For bytes, we already handled above; here idx>=1
        suffix = gnu_suffixes[idx]
        # GNU often formats with no decimals when possible but
        # we'll keep the provided format and then strip trailing .0
        out = (format % value)
        if out.endswith(".0"):
            out = out[:-2]
        return f"{prefix}{out}{suffix}"

    # Normal style with space and full unit
    unit = units[idx]
    out = (format % value)
    return f"{prefix}{out} {unit}"