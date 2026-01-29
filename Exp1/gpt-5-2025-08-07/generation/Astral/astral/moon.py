from datetime import datetime, date as date_cls, timezone
from typing import Union, Optional

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


# Synodic month in days (new moon to new moon)
SYNODIC_MONTH = 29.530588853

# Reference new moon epoch: 2000-01-06 18:14 UTC (approx)
REF_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)


def _coerce_tzinfo(tzinfo: Optional[Union[str, timezone]]) -> Optional[timezone]:
    if tzinfo is None:
        return None
    if isinstance(tzinfo, timezone):
        return tzinfo
    if isinstance(tzinfo, str):
        if ZoneInfo is None:
            return timezone.utc
        try:
            return ZoneInfo(tzinfo)
        except Exception:
            return timezone.utc
    return tzinfo  # type: ignore


def phase(d: Union[date_cls, datetime]) -> int:
    """
    Returns the lunar phase as an integer day in the cycle: 0..29 inclusive.

    The value increases monotonically day-to-day and wraps at new moon.
    This provides a stable and simple approximation suitable for many uses.
    """
    if isinstance(d, datetime):
        # Convert to UTC to compute days since epoch consistently
        dt_utc = d.astimezone(timezone.utc)
    else:
        # Treat given date as midnight in UTC
        dt_utc = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)

    delta_days = (dt_utc - REF_NEW_MOON).total_seconds() / 86400.0
    # Normalize to [0, SYNODIC_MONTH)
    cycle_pos = delta_days % SYNODIC_MONTH
    # Return integer day in cycle 0..29
    return int(cycle_pos // 1.0)