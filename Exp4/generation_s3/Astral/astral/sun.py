from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Dict, Optional

from .utils import (
    _coerce_tzinfo,
    _date_from_any,
    _duck_observer,
    _julian_century,
    _julian_day,
    _equation_of_time_minutes,
    _sun_declination,
    _hour_angle_deg,
    _aware_datetime_on_date,
)

# Standard apparent sunrise/sunset zenith (includes refraction and solar radius)
_STANDARD_SUNRISE_ZENITH = 90.833  # degrees


def _solar_times_minutes(latitude: float, longitude: float, d: date, tzinfo, solar_zenith: float):
    """Return (dawn/dusk or sunrise/sunset) minutes from local midnight for given zenith.

    Uses NOAA algorithm with equation of time and solar declination at solar noon.
    """
    tz = _coerce_tzinfo(tzinfo)

    # Use local noon as the reference moment to compute declination/EoT for this date.
    local_noon = datetime(d.year, d.month, d.day, 12, 0, 0, tzinfo=tz)
    noon_utc = local_noon.astimezone(timezone.utc)
    T = _julian_century(_julian_day(noon_utc))

    eq_time = _equation_of_time_minutes(T)
    solar_dec = _sun_declination(T)

    ha = _hour_angle_deg(latitude, solar_dec, solar_zenith)
    # If sun never reaches required zenith, hour angle may be 0/180 depending on clamp.
    # Detect polar day/night by checking the unclamped feasibility.
    # Compute cosH without clamping by reusing formula inline.
    import math
    lat_r = math.radians(latitude)
    dec_r = math.radians(solar_dec)
    zen_r = math.radians(solar_zenith)
    cosH_raw = (math.cos(zen_r) - math.sin(lat_r) * math.sin(dec_r)) / (math.cos(lat_r) * math.cos(dec_r))

    if cosH_raw > 1.0:
        raise ValueError("Sun never rises on this date at this location.")
    if cosH_raw < -1.0:
        raise ValueError("Sun never sets on this date at this location.")

    solar_noon_min = 720.0 - (4.0 * longitude) - eq_time
    sunrise_min = solar_noon_min - (ha * 4.0)
    sunset_min = solar_noon_min + (ha * 4.0)
    return sunrise_min, sunset_min, solar_noon_min


def _get_tz_for_date_param(date_param, tzinfo):
    # Determine tz used to interpret "today" and datetime inputs.
    return _coerce_tzinfo(tzinfo)


def sun(observer, date=None, tzinfo=None, dawn_dusk_depression: float = 6.0) -> Dict[str, datetime]:
    tz = _coerce_tzinfo(tzinfo)
    d = _date_from_any(date, tz)

    lat, lon, _elev = _duck_observer(observer)

    # Dawn/dusk: depression angle below horizon => zenith = 90 + depression
    twilight_zenith = 90.0 + float(dawn_dusk_depression)

    sunrise_min, sunset_min, noon_min = _solar_times_minutes(lat, lon, d, tz, _STANDARD_SUNRISE_ZENITH)
    dawn_min, dusk_min, _ = _solar_times_minutes(lat, lon, d, tz, twilight_zenith)

    return {
        "dawn": _aware_datetime_on_date(d, dawn_min, tz),
        "sunrise": _aware_datetime_on_date(d, sunrise_min, tz),
        "noon": _aware_datetime_on_date(d, noon_min, tz),
        "sunset": _aware_datetime_on_date(d, sunset_min, tz),
        "dusk": _aware_datetime_on_date(d, dusk_min, tz),
    }


def sunrise(observer, date=None, tzinfo=None) -> datetime:
    return sun(observer, date=date, tzinfo=tzinfo)["sunrise"]


def sunset(observer, date=None, tzinfo=None) -> datetime:
    return sun(observer, date=date, tzinfo=tzinfo)["sunset"]


def noon(observer, date=None, tzinfo=None) -> datetime:
    return sun(observer, date=date, tzinfo=tzinfo)["noon"]


def dawn(observer, date=None, tzinfo=None, depression: float = 6.0) -> datetime:
    return sun(observer, date=date, tzinfo=tzinfo, dawn_dusk_depression=depression)["dawn"]


def dusk(observer, date=None, tzinfo=None, depression: float = 6.0) -> datetime:
    return sun(observer, date=date, tzinfo=tzinfo, dawn_dusk_depression=depression)["dusk"]