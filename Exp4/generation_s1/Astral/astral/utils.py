from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional, Union

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None


def _to_date(d: Optional[Union[date, datetime]]) -> date:
    if d is None:
        raise TypeError("date cannot be None here")
    if isinstance(d, datetime):
        return d.date()
    return d


def _resolve_tzinfo(tzinfo, observer=None):
    if tzinfo is None:
        # If the observer looks like a LocationInfo, use its timezone.
        if observer is not None:
            tz = getattr(observer, "timezone", None)
            if isinstance(tz, str) and tz:
                return _resolve_tzinfo(tz, None)
            tz2 = getattr(observer, "tzinfo", None)
            if tz2 is not None:
                # tzinfo property might return ZoneInfo or None
                if hasattr(tz2, "utcoffset"):
                    return tz2
        return timezone.utc

    if isinstance(tzinfo, str):
        if ZoneInfo is None:
            return timezone.utc
        return ZoneInfo(tzinfo)

    return tzinfo


def _today_in_tz(tzinfo) -> date:
    return datetime.now(tzinfo).date()


def _local_midnight(d: date, tzinfo) -> datetime:
    return datetime.combine(d, time(0, 0, 0), tzinfo=tzinfo)


def _round_to_second(dt: datetime) -> datetime:
    # Round half-up to nearest second
    us = dt.microsecond
    if us >= 500_000:
        dt = dt + timedelta(seconds=1)
    return dt.replace(microsecond=0)


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _deg_to_rad(x: float) -> float:
    return x * math.pi / 180.0


def _rad_to_deg(x: float) -> float:
    return x * 180.0 / math.pi


def _normalize_deg(angle: float) -> float:
    angle = angle % 360.0
    if angle < 0:
        angle += 360.0
    return angle


def _earth_dip_degrees(elevation_m: float) -> float:
    # Approximate dip of horizon in degrees; common approximation:
    # dip(deg) ≈ 0.0347 * sqrt(height_m)
    if elevation_m <= 0:
        return 0.0
    return 0.0347 * math.sqrt(elevation_m)