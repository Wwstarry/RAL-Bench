from __future__ import annotations

from decimal import Decimal
from typing import Any


def naturalsize(
    value: Any,
    binary: bool = False,
    format: str = "%.1f",
    suffix: str = "B",
    gnuradio: bool = False,
) -> str:
    if value is None:
        raise TypeError("value must not be None")

    # Convert to Decimal for stable scaling/formatting.
    try:
        d = Decimal(str(value))
    except Exception:
        # If it's not numeric, let it raise TypeError in Decimal or return str.
        return f"{value} {suffix}".rstrip()

    sign = "-" if d.is_signed() and d != 0 else ""
    d = abs(d)

    base = Decimal(1024) if binary else Decimal(1000)

    if gnuradio:
        # GNU Radio style units: no trailing "B"
        units = ["", "K", "M", "G", "T", "P", "E"]
        unit_suffix = ""
        # For bytes, they often still show "B"; keep compatibility with our suffix
        # behavior: if suffix provided, keep it only for the base unit.
    else:
        if binary:
            units = ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei"]
        else:
            units = ["", "k", "M", "G", "T", "P", "E"]
        unit_suffix = suffix

    # Bytes case: < base uses integer
    if d < base:
        # Always show as integer bytes with unit "B" (or suffix if customized)
        # The unit should be just suffix if provided; default produces "B".
        unit = suffix if suffix else ""
        num = str(int(d))
        if gnuradio:
            # For gnuradio, base unit is "B" if suffix is "B"
            unit = suffix if suffix else ""
        return (f"{sign}{num} {unit}").rstrip()

    idx = 0
    q = d
    max_idx = len(units) - 1
    while q >= base and idx < max_idx:
        q = q / base
        idx += 1

    unit = units[idx]
    if gnuradio:
        # For gnuradio, bytes are not reached here; units are K/M/G...
        # The suffix argument is ignored in this mode for scaled units.
        out_unit = unit
    else:
        out_unit = f"{unit}{unit_suffix}" if unit or unit_suffix else unit

    # Apply formatting to the scaled number; use float formatting for printf style.
    # Decimal -> float is safe for typical values used in tests.
    num = format % float(q)

    return f"{sign}{num} {out_unit}".rstrip()