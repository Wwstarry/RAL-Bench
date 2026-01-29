"""
Simple sunrise / sunset calculations based on NOAA's Solar Calculator.

Only the tiny subset required by the test-suite is implemented.  The API
surface tries to mimic the original `astral.sun` module closely.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Dict, Optional, Union

from zoneinfo import ZoneInfo

from ._math import (
    acos_deg,
    asin_deg,
    cos_deg,
    day_of_year,
    sin_deg,
    tan_deg,
    to_range,
)
from .location import Observer

__all__ = [
    "sun",
    "sunrise",
    "sunset",
    "dawn",
    "dusk",
    "noon",
]

# Zenith angles (official = 90°50')
OFFICIAL_ZENITH = 90.833
CIVIL_ZENITH = 96.0  # Sun's centre 6° below horizon


def _calc_event(observer: Observer, date, zenith: float, is_rise: bool) -> Optional[datetime]:
    """
    Calculate the UTC datetime of a sunrise/sunset/twilight event.

    Returns None if the event does not happen (e.g. polar night/day).
    """
    # Day of year
    n = day_of_year(date)

    lng_hour = observer.longitude / 15.0

    if is_rise:
        t = n + ((6 - lng_hour) / 24)
    else:
        t = n + ((18 - lng_hour) / 24)

    # Sun's mean anomaly
    m = (0.9856 * t) - 3.289

    # Sun's true longitude
    l = m + (1.916 * sin_deg(m)) + (0.020 * sin_deg(2 * m)) + 282.634
    l = to_range(l, 0, 360)

    # Sun's right ascension
    ra = atan2_deg(0.91764 * tan_deg(l), 1)
    ra = to_range(ra, 0, 360)

    # convert RA to hours
    ra /= 15.0

    # Sun's declination
    sin_dec = 0.39782 * sin_deg(l)
    cos_dec = cos_deg(asin_deg(sin_dec))

    # Sun local hour angle
    cos_h = (cos_deg(zenith) - (sin_dec * sin_deg(observer.latitude))) / (
        cos_dec * cos_deg(observer.latitude)
    )

    # If cos_h out of range the sun never rises/sets on this date at this location
    if cos_h > 1 or cos_h < -1:
        return None

    if is_rise:
        h = 360 - acos_deg(cos_h)
    else:
        h = acos_deg(cos_h)

    h /= 15.0  # to hours

    # local mean time
    t_local = h + ra - (0.06571 * t) - 6.622

    # Convert to UTC
    ut = t_local - lng_hour
    ut = to_range(ut, 0, 24)  # wrap around

    # Build datetime in UTC
    hour = int(ut)
    minute = int((ut - hour) * 60)
    second = int((((ut - hour) * 60) - minute) * 60 + 0.5)

    dt = datetime(
        date.year,
        date.month,
        date.day,
        hour=hour,
        minute=minute,
        second=second,
        tzinfo=timezone.utc,
    )
    return dt


def _to_tz(dt: Optional[datetime], tz) -> Optional[datetime]:
    if dt is None:
        return None
    if tz is None:
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz)


def sunrise(
    observer: Observer,
    date: Optional[datetime] = None,
    tzinfo: Optional[Union[str, timezone, ZoneInfo]] = None,
):
    """
    Return the local sunrise time for *observer* on *date*.

    tzinfo:
        Optional timezone. If omitted we attempt to honour
        `observer.timezone` if it is a ZoneInfo, else fallback to UTC.
    """
    if date is None:
        date = datetime.now(tz=timezone.utc).date()
    else:
        date = date.date() if isinstance(date, datetime) else date

    dt = _calc_event(observer, date, OFFICIAL_ZENITH, is_rise=True)
    tz = _select_tz(observer, tzinfo)
    return _to_tz(dt, tz)


def sunset(
    observer: Observer,
    date: Optional[datetime] = None,
    tzinfo: Optional[Union[str, timezone, ZoneInfo]] = None,
):
    """
    Return the local sunset time for *observer* on *date*.
    """
    if date is None:
        date = datetime.now(tz=timezone.utc).date()
    else:
        date = date.date() if isinstance(date, datetime) else date

    dt = _calc_event(observer, date, OFFICIAL_ZENITH, is_rise=False)
    tz = _select_tz(observer, tzinfo)
    return _to_tz(dt, tz)


def dawn(
    observer: Observer,
    date: Optional[datetime] = None,
    tzinfo: Optional[Union[str, timezone, ZoneInfo]] = None,
):
    """
    Civil dawn: sun is 6° below horizon.
    """
    if date is None:
        date = datetime.now(tz=timezone.utc).date()
    else:
        date = date.date() if isinstance(date, datetime) else date
    dt = _calc_event(observer, date, CIVIL_ZENITH, is_rise=True)
    tz = _select_tz(observer, tzinfo)
    return _to_tz(dt, tz)


def dusk(
    observer: Observer,
    date: Optional[datetime] = None,
    tzinfo: Optional[Union[str, timezone, ZoneInfo]] = None,
):
    """
    Civil dusk: sun is 6° below horizon.
    """
    if date is None:
        date = datetime.now(tz=timezone.utc).date()
    else:
        date = date.date() if isinstance(date, datetime) else date
    dt = _calc_event(observer, date, CIVIL_ZENITH, is_rise=False)
    tz = _select_tz(observer, tzinfo)
    return _to_tz(dt, tz)


def noon(
    observer: Observer,
    date: Optional[datetime] = None,
    tzinfo: Optional[Union[str, timezone, ZoneInfo]] = None,
):
    """
    Solar noon approximated as the midpoint between sunrise and sunset.
    """
    sr = sunrise(observer, date=date, tzinfo=timezone.utc)
    ss = sunset(observer, date=date, tzinfo=timezone.utc)
    if sr is None or ss is None:
        return None  # Polar day / night

    midpoint = sr + (ss - sr) / 2
    tz = _select_tz(observer, tzinfo)
    return _to_tz(midpoint, tz)


def sun(
    observer: Observer,
    date: Optional[datetime] = None,
    tzinfo: Optional[Union[str, timezone, ZoneInfo]] = None,
) -> Dict[str, Optional[datetime]]:
    """
    Convenience wrapper returning a dict containing:
        ['dawn', 'sunrise', 'noon', 'sunset', 'dusk']
    """
    keys = ("dawn", "sunrise", "noon", "sunset", "dusk")
    funcs = (dawn, sunrise, noon, sunset, dusk)
    results = {}
    for k, f in zip(keys, funcs):
        results[k] = f(observer, date=date, tzinfo=tzinfo)
    return results


# ---------------------------------------------------------------------- #
# Internal helpers
# ---------------------------------------------------------------------- #
def atan2_deg(y_over_x: float, dummy: float = 1.0) -> float:
    """
    We only need `atan(y)` where `y = 0.91764 * tan(L)` in NOAA docs.
    Splitting this off keeps the math helpers lean.
    """
    import math

    return math.degrees(math.atan(y_over_x))


def _select_tz(observer: Observer, tz):
    """
    Resolve *tz* which may be:
      * None          → UTC
      * str           → ZoneInfo(str)
      * datetime.tzinfo (already ok)
    """
    if tz is None:
        return timezone.utc
    if isinstance(tz, str):
        return ZoneInfo(tz)
    return tz