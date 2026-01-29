from __future__ import annotations

from datetime import date, datetime, timezone

from .utils import _date_from_any, _coerce_tzinfo

_SYNODIC_MONTH = 29.530588853  # days
# Reference new moon epoch: 2000-01-06 18:14 UTC (commonly used)
_EPOCH = datetime(2000, 1, 6, 18, 14, 0, tzinfo=timezone.utc)


def phase(date=None) -> float:
    """Return lunar phase as days into the synodic month [0, 29.53..].

    Deterministic and stable: computed from an epoch new moon and synodic month.
    Uses UTC noon of the provided date to reduce timezone edge effects.
    """
    if date is None:
        d = datetime.now(timezone.utc).date()
    else:
        if isinstance(date, datetime):
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            date = date.astimezone(timezone.utc)
            d = date.date()
        elif isinstance(date, date.__class__) and isinstance(date, date):
            d = date
        else:
            # fall back to shared parser for date/datetime; interpret in UTC
            d = _date_from_any(date, timezone.utc)

    dt = datetime(d.year, d.month, d.day, 12, 0, 0, tzinfo=timezone.utc)
    days = (dt - _EPOCH).total_seconds() / 86400.0
    p = days % _SYNODIC_MONTH
    # Clamp very small numerical drift
    if p < 0.0:
        p += _SYNODIC_MONTH
    if p > _SYNODIC_MONTH:
        p = p % _SYNODIC_MONTH
    return float(p)