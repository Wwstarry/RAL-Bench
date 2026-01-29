from __future__ import annotations

from datetime import datetime as _dt_datetime
from typing import Optional


def _plural(value: int, unit: str) -> str:
    if abs(value) == 1:
        return f"{value} {unit}"
    return f"{value} {unit}s"


def diff_for_humans(
    dt: _dt_datetime,
    other: Optional[_dt_datetime] = None,
    absolute: bool = False,
) -> str:
    """
    Human readable difference between datetimes.

    Examples:
    - "1 second ago"
    - "in 2 hours"
    - "3 days ago"
    """
    from datetime import datetime as _datetime

    if other is None:
        other = _datetime.now(dt.tzinfo) if dt.tzinfo else _datetime.now()

    # convert both to same frame if possible
    if dt.tzinfo is not None and other.tzinfo is not None:
        other = other.astimezone(dt.tzinfo)

    delta = dt - other
    seconds = int(delta.total_seconds())
    future = seconds > 0
    seconds = abs(seconds)

    if seconds < 5:
        phrase = "just now"
        return phrase if absolute else phrase

    units = [
        ("year", 365 * 24 * 3600),
        ("month", 30 * 24 * 3600),
        ("week", 7 * 24 * 3600),
        ("day", 24 * 3600),
        ("hour", 3600),
        ("minute", 60),
        ("second", 1),
    ]

    for unit, unit_seconds in units:
        if seconds >= unit_seconds:
            value = seconds // unit_seconds
            text = _plural(int(value), unit)
            if absolute:
                return text
            return f"in {text}" if future else f"{text} ago"

    # fallback
    text = _plural(0, "second")
    if absolute:
        return text
    return f"in {text}" if future else f"{text} ago"