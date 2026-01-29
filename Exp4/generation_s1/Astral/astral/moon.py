from __future__ import annotations

from datetime import date, datetime
from typing import Union

# Synodic month (mean) in days
_SYNODIC_MONTH = 29.53058867

# Reference new moon epoch near Astral/common implementations:
# 2000-01-06 18:14 UTC is a commonly used reference; we use date-based noon to avoid jitter.
# We'll compute age from a fixed day count with a fractional offset representing the time.
_EPOCH_ORDINAL = date(2000, 1, 6).toordinal()
# 18:14 UTC expressed as fraction of day:
_EPOCH_FRACTION = (18 + 14 / 60.0) / 24.0


def phase(d: Union[date, datetime]) -> float:
    """Return lunar phase as age in days within [0, synodic_month).

    Input may be a date or datetime. If datetime, its date component is used.

    The result is stable and monotonic day-to-day (modulo wrap at new moon).
    """
    if isinstance(d, datetime):
        d = d.date()

    # Use noon to reduce discontinuities and align with common simple algorithms.
    days_since_epoch = (d.toordinal() - _EPOCH_ORDINAL) + (0.5 - _EPOCH_FRACTION)
    age = days_since_epoch % _SYNODIC_MONTH
    # Ensure numeric within [0, synodic_month)
    if age < 0:
        age += _SYNODIC_MONTH
    return float(age)