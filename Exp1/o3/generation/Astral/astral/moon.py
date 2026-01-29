"""
A very small moon phase implementation.

The calculation is *extremely* simplified but good enough for the
basic property tests it is intended to satisfy.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

__all__ = ["phase"]


# Reference new moon: 2000-01-06 18:14 UTC (Julian Day 2451550.1)
_REF_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
_SYNODIC_MONTH = 29.530588853  # days


def phase(date) -> float:
    """
    Return the lunar phase for *date* (0 = new moon, 14-15 = full moon, 29 = new).

    The returned value corresponds roughly to the moon age in days and is
    guaranteed to be monotonically increasing (modulo 29.53) for consecutive
    days.
    """
    if isinstance(date, datetime):
        dt = date.astimezone(timezone.utc)
    else:
        # date is a datetime.date
        dt = datetime(date.year, date.month, date.day, tzinfo=timezone.utc)

    delta = dt - _REF_NEW_MOON
    days = delta.total_seconds() / 86400.0
    phase = days % _SYNODIC_MONTH
    # Ensure within 0-29.53 range
    return phase