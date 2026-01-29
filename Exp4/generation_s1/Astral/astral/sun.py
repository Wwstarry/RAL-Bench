from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional, Union

from .errors import SunNeverRisesError, SunNeverSetsError
from .utils import (
    _clamp,
    _deg_to_rad,
    _earth_dip_degrees,
    _local_midnight,
    _normalize_deg,
    _rad_to_deg,
    _resolve_tzinfo,
    _round_to_second,
    _today_in_tz,
)

DateLike = Union[date, datetime]


def _get_observer_fields(observer: Any):
    lat = float(getattr(observer, "latitude"))
    lon = float(getattr(observer, "longitude"))
    elev = float(getattr(observer, "elevation", 0.0))
    return lat, lon, elev


def _day_of_year(d: date) -> int:
    return d.timetuple().tm_yday


def _fractional_year_gamma(d: date) -> float:
    # NOAA approximation uses gamma = 2*pi/365 * (N-1)
    n = _day_of_year(d)
    return 2.0 * math.pi / 365.0 * (n - 1)


def _equation_of_time_minutes(gamma: float) -> float:
    # NOAA approximation (minutes)
    return 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )


def _solar_declination_rad(gamma: float) -> float:
    # NOAA approximation (radians)
    return (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2 * gamma)
        + 0.000907 * math.sin(2 * gamma)
        - 0.002697 * math.cos(3 * gamma)
        + 0.00148 * math.sin(3 * gamma)
    )


def _hour_angle_deg(lat_deg: float, decl_rad: float, solar_altitude_deg: float):
    # cos(H) = (sin(alt) - sin(lat)*sin(dec)) / (cos(lat)*cos(dec))
    lat_rad = _deg_to_rad(lat_deg)
    alt_rad = _deg_to_rad(solar_altitude_deg)

    sin_lat = math.sin(lat_rad)
    cos_lat = math.cos(lat_rad)
    sin_dec = math.sin(decl_rad)
    cos_dec = math.cos(decl_rad)

    denom = cos_lat * cos_dec
    # At poles denom can be ~0; handle via clamp and later checks.
    if abs(denom) < 1e-12:
        denom = 1e-12 if denom >= 0 else -1e-12

    cos_h = (math.sin(alt_rad) - sin_lat * sin_dec) / denom
    # Determine never rises/sets based on cos_h out of [-1,1]
    if cos_h > 1.0:
        return None, "never_rises"
    if cos_h < -1.0:
        return None, "never_sets"
    cos_h = _clamp(cos_h, -1.0, 1.0)
    h = math.acos(cos_h)
    return _rad_to_deg(h), None


def _events(observer: Any, d: date, tzinfo, dawn_dusk_depression: float = 6.0) -> Dict[str, datetime]:
    lat, lon, elev = _get_observer_fields(observer)

    tzinfo = _resolve_tzinfo(tzinfo, observer)
    midnight = _local_midnight(d, tzinfo)

    # Use noon local time to get an offset representative for that date (DST-safe).
    midday = midnight + timedelta(hours=12)
    offset = midday.utcoffset() or timedelta(0)
    tz_offset_min = offset.total_seconds() / 60.0

    gamma = _fractional_year_gamma(d)
    eq_time = _equation_of_time_minutes(gamma)
    decl = _solar_declination_rad(gamma)

    # Solar noon in local minutes from midnight:
    # minutes = 720 - 4*longitude - EoT + tz_offset_minutes
    solar_noon_min = 720.0 - 4.0 * lon - eq_time + tz_offset_min

    dip = _earth_dip_degrees(elev)

    # Sunrise/sunset apparent altitude includes refraction and solar radius.
    # Adjust by horizon dip: a higher observer sees the sun earlier.
    sunrise_alt = -0.833 - dip
    twilight_alt = -float(dawn_dusk_depression) - dip

    ha_sun, err_sun = _hour_angle_deg(lat, decl, sunrise_alt)
    if err_sun == "never_rises":
        raise SunNeverRisesError("Sun never rises on this date at this location")
    if err_sun == "never_sets":
        raise SunNeverSetsError("Sun never sets on this date at this location")

    ha_twi, err_twi = _hour_angle_deg(lat, decl, twilight_alt)
    if err_twi == "never_rises":
        # If sun never rises, twilight also never occurs for deeper altitude; keep consistent.
        raise SunNeverRisesError("Sun never rises on this date at this location")
    if err_twi == "never_sets":
        raise SunNeverSetsError("Sun never sets on this date at this location")

    sunrise_min = solar_noon_min - 4.0 * ha_sun
    sunset_min = solar_noon_min + 4.0 * ha_sun
    dawn_min = solar_noon_min - 4.0 * ha_twi
    dusk_min = solar_noon_min + 4.0 * ha_twi

    def at_minutes(m: float) -> datetime:
        dt = midnight + timedelta(minutes=float(m))
        return _round_to_second(dt)

    return {
        "dawn": at_minutes(dawn_min),
        "sunrise": at_minutes(sunrise_min),
        "noon": at_minutes(solar_noon_min),
        "sunset": at_minutes(sunset_min),
        "dusk": at_minutes(dusk_min),
    }


def sun(
    observer: Any,
    date: Optional[DateLike] = None,
    tzinfo=None,
    dawn_dusk_depression: float = 6.0,
) -> Dict[str, datetime]:
    tz = _resolve_tzinfo(tzinfo, observer)
    if date is None:
        d = _today_in_tz(tz)
    else:
        d = date.date() if isinstance(date, datetime) else date
    return _events(observer, d, tz, dawn_dusk_depression=dawn_dusk_depression)


def dawn(observer: Any, date: Optional[DateLike] = None, tzinfo=None, depression: float = 6.0) -> datetime:
    return sun(observer, date=date, tzinfo=tzinfo, dawn_dusk_depression=depression)["dawn"]


def sunrise(observer: Any, date: Optional[DateLike] = None, tzinfo=None) -> datetime:
    return sun(observer, date=date, tzinfo=tzinfo)["sunrise"]


def noon(observer: Any, date: Optional[DateLike] = None, tzinfo=None) -> datetime:
    return sun(observer, date=date, tzinfo=tzinfo)["noon"]


def sunset(observer: Any, date: Optional[DateLike] = None, tzinfo=None) -> datetime:
    return sun(observer, date=date, tzinfo=tzinfo)["sunset"]


def dusk(observer: Any, date: Optional[DateLike] = None, tzinfo=None, depression: float = 6.0) -> datetime:
    return sun(observer, date=date, tzinfo=tzinfo, dawn_dusk_depression=depression)["dusk"]