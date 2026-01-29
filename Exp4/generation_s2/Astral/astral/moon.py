from __future__ import annotations

import math
from datetime import date as Date, datetime, timezone


def _julian_day_at_noon(d: Date) -> float:
    # Use 12:00 UTC to reduce issues around day boundaries.
    dt = datetime(d.year, d.month, d.day, 12, 0, 0, tzinfo=timezone.utc)
    y = dt.year
    m = dt.month
    day = dt.day + (dt.hour / 24.0)

    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + day + b - 1524.5
    return jd


def phase(d: Date | datetime) -> float:
    """Return lunar phase as a number in [0, 29.53).

    0 is (near) new moon, ~14.77 is (near) full moon.
    Monotonic day-to-day for consecutive dates (small numerical noise aside).
    """
    if isinstance(d, datetime):
        d = d.date()

    jd = _julian_day_at_noon(d)

    # Simple synodic month approximation using a known new moon epoch.
    # Epoch: 2000-01-06 18:14 UTC (JD ~ 2451550.1)
    synodic_month = 29.530588853
    days_since = jd - 2451550.1
    lunations = days_since / synodic_month
    frac = lunations - math.floor(lunations)
    age = frac * synodic_month

    # Ensure within range [0, synodic_month)
    if age < 0:
        age += synodic_month
    elif age >= synodic_month:
        age -= synodic_month

    return float(age)