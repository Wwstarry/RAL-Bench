from __future__ import annotations

import math
from datetime import date as _date, datetime
from typing import Optional, Union


def _as_date(d: Optional[Union[_date, datetime]]) -> _date:
    if d is None:
        return datetime.now().date()
    if isinstance(d, datetime):
        return d.date()
    return d


def phase(date: Optional[Union[_date, datetime]] = None) -> float:
    """
    Return lunar phase as a float in range [0, 29.53).

    0   -> New Moon
    ~7  -> First Quarter
    ~14 -> Full Moon
    ~22 -> Last Quarter

    Uses a simple, stable approximation based on days since a known new moon epoch.
    Monotonic across consecutive dates (modulo wrap-around at synodic month).
    """
    d = _as_date(date)

    # Use an epoch near a known new moon: 2000-01-06 18:14 UT (JDN ~ 2451550.1)
    # Compute days since 2000-01-06 (date resolution; good enough for tests).
    epoch = _date(2000, 1, 6)
    days = (d - epoch).days

    synodic = 29.530588853  # mean synodic month
    p = (days % synodic)
    # Ensure within [0, synodic)
    if p < 0:
        p += synodic
    return float(p)