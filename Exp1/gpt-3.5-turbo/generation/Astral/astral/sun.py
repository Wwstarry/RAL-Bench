"""
Sun calculation functions compatible with Astral core API.
"""

from datetime import datetime, timedelta, time, timezone
from math import cos, sin, tan, acos, asin, atan2, radians, degrees, floor
from typing import Optional, Dict
import zoneinfo

from astral.location import Observer

# Constants
ZENITH_OFFICIAL = 90.8333  # official zenith for sunrise/sunset (degrees)

def _to_julian_day(dt: datetime) -> float:
    """
    Convert a datetime to Julian Day.
    """
    # Algorithm from Astronomical Algorithms by Jean Meeus
    year = dt.year
    month = dt.month
    day = dt.day
    hour = dt.hour + dt.minute / 60 + dt.second / 3600 + dt.microsecond / 3_600_000_000

    if month <= 2:
        year -= 1
        month += 12

    A = floor(year / 100)
    B = 2 - A + floor(A / 4)

    JD = floor(365.25 * (year + 4716)) + floor(30.6001 * (month + 1)) + day + B - 1524.5 + hour / 24.0
    return JD

def _from_julian_day(jd: float) -> datetime:
    """
    Convert Julian Day to datetime in UTC.
    """
    # Algorithm from Astronomical Algorithms by Jean Meeus
    jd += 0.5
    Z = int(jd)
    F = jd - Z
    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - int(alpha / 4)
    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)

    day = B - D - int(30.6001 * E) + F
    month = E - 1 if E < 14 else E - 13
    year = C - 4716 if month > 2 else C - 4715

    day_floor = int(day)
    day_fraction = day - day_floor
    hours = day_fraction * 24
    hour = int(hours)
    minutes = (hours - hour) * 60
    minute = int(minutes)
    seconds = (minutes - minute) * 60
    second = int(seconds)
    microsecond = int((seconds - second) * 1_000_000)

    return datetime(year, month, day_floor, hour, minute, second, microsecond, tzinfo=timezone.utc)

def _sun_mean_anomaly(d: float) -> float:
    """
    Mean anomaly of the Sun (degrees).
    """
    return (357.5291 + 0.98560028 * d) % 360

def _sun_equation_of_center(M: float) -> float:
    """
    Sun's equation of center (degrees).
    """
    Mrad = radians(M)
    return (1.9148 * sin(Mrad) + 0.0200 * sin(2 * Mrad) + 0.0003 * sin(3 * Mrad))

def _sun_true_longitude(M: float, C: float) -> float:
    """
    Sun's true longitude (degrees).
    """
    L0 = (M + C + 180 + 102.9372) % 360
    return L0

def _sun_declination(L: float) -> float:
    """
    Sun's declination (radians).
    """
    return asin(sin(radians(L)) * sin(radians(23.44)))

def _hour_angle(latitude: float, declination: float, zenith: float) -> Optional[float]:
    """
    Calculate the hour angle for the sun at the given zenith.
    Returns hour angle in degrees or None if sun never rises/sets.
    """
    lat_rad = radians(latitude)
    zenith_rad = radians(zenith)
    cos_ha = (cos(zenith_rad) - sin(lat_rad) * sin(declination)) / (cos(lat_rad) * cos(declination))
    if cos_ha > 1:
        # Sun never rises on this location (polar night)
        return None
    elif cos_ha < -1:
        # Sun never sets on this location (midnight sun)
        return None
    else:
        return degrees(acos(cos_ha))

def _solar_noon_utc(d: float, longitude: float) -> float:
    """
    Calculate solar noon in UTC as Julian day fraction.
    """
    # Approximate solar noon
    Jtransit = 2451545.0 + d - longitude / 360.0
    return Jtransit

def _sun_times(observer: Observer, date: datetime, tzinfo) -> Dict[str, datetime]:
    """
    Calculate sun times for the given observer and date.
    Returns dict with keys: dawn, sunrise, noon, sunset, dusk.
    """
    # Convert date to datetime at midnight UTC
    date_utc = datetime(date.year, date.month, date.day, tzinfo=tzinfo)
    # Convert date to UTC midnight
    if tzinfo is not None:
        date_utc = date_utc.astimezone(zoneinfo.ZoneInfo("UTC"))
    else:
        date_utc = date_utc.replace(tzinfo=timezone.utc)

    # Julian day at 0h UTC
    JD = _to_julian_day(date_utc)

    # Days since J2000.0
    d = JD - 2451545.0

    # Mean anomaly
    M = _sun_mean_anomaly(d)

    # Equation of center
    C = _sun_equation_of_center(M)

    # True longitude
    L = _sun_true_longitude(M, C)

    # Declination
    decl = _sun_declination(L)

    # Solar noon (approximate)
    Jnoon = 2451545.0 + d - observer.longitude / 360.0

    # Hour angle for sunrise/sunset
    ha = _hour_angle(observer.latitude, decl, ZENITH_OFFICIAL)
    if ha is None:
        # Polar day or night: no sunrise or sunset
        # Return None for sunrise and sunset, noon at solar noon
        noon_dt = _from_julian_day(Jnoon).astimezone(tzinfo)
        return {
            "dawn": None,
            "sunrise": None,
            "noon": noon_dt,
            "sunset": None,
            "dusk": None,
        }

    # Calculate sunrise and sunset Julian days
    Jset = Jnoon + ha / 360.0
    Jrise = Jnoon - ha / 360.0

    # Dawn and dusk: civil twilight (zenith 96 degrees)
    ha_civil = _hour_angle(observer.latitude, decl, 96.0)
    if ha_civil is None:
        dawn_dt = None
        dusk_dt = None
    else:
        Jdawn = Jnoon - ha_civil / 360.0
        Jdusk = Jnoon + ha_civil / 360.0
        dawn_dt = _from_julian_day(Jdawn).astimezone(tzinfo)
        dusk_dt = _from_julian_day(Jdusk).astimezone(tzinfo)

    sunrise_dt = _from_julian_day(Jrise).astimezone(tzinfo)
    sunset_dt = _from_julian_day(Jset).astimezone(tzinfo)
    noon_dt = _from_julian_day(Jnoon).astimezone(tzinfo)

    return {
        "dawn": dawn_dt,
        "sunrise": sunrise_dt,
        "noon": noon_dt,
        "sunset": sunset_dt,
        "dusk": dusk_dt,
    }

def sun(observer: Observer, date: Optional[datetime] = None, tzinfo=None) -> Dict[str, datetime]:
    """
    Calculate sun times for the given observer and date.
    Returns dict with keys: dawn, sunrise, noon, sunset, dusk.
    """
    if date is None:
        date = datetime.now(tz=tzinfo)
    # Normalize date to date only
    date = date.date() if hasattr(date, "date") else date
    # Convert date to datetime at midnight in tzinfo
    if tzinfo is None:
        tzinfo = timezone.utc
    dt = datetime(date.year, date.month, date.day, tzinfo=tzinfo)
    return _sun_times(observer, dt, tzinfo)

def sunrise(observer: Observer, date: Optional[datetime] = None, tzinfo=None) -> Optional[datetime]:
    """
    Calculate sunrise time for the given observer and date.
    """
    s = sun(observer, date, tzinfo)
    return s["sunrise"]

def sunset(observer: Observer, date: Optional[datetime] = None, tzinfo=None) -> Optional[datetime]:
    """
    Calculate sunset time for the given observer and date.
    """
    s = sun(observer, date, tzinfo)
    return s["sunset"]