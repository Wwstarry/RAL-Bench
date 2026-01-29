"""
Functions for computing dawn, sunrise, noon, sunset and dusk times
in a manner compatible with the reference Astral library.

Implements a simplified version of the NOAA solar equations,
sufficient for test scenarios.
"""

import math
import datetime
from datetime import datetime as dt, timedelta
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback for older Python
    from datetime import timezone as ZoneInfo

# Constants for solar calculations
# For the top of the Sun disk: ~ 0.83, but we keep it as default
SUN_APPARENT_RADIUS = 0.8333
CIVIL_TWILIGHT_DEGREES = 6.0  # for dawn/dusk

def _to_radians(deg):
    return math.pi * deg / 180.0

def _to_degrees(rad):
    return 180.0 * rad / math.pi

def _utc_to_tz(naive_utc, tzinfo):
    """Convert a naive UTC datetime to the specified tzinfo."""
    if tzinfo is None:
        return naive_utc.replace(tzinfo=datetime.timezone.utc)
    if isinstance(tzinfo, str):
        tzinfo = ZoneInfo(tzinfo)
    return naive_utc.replace(tzinfo=datetime.timezone.utc).astimezone(tzinfo)

def _date_to_julian_day(d: datetime.date) -> float:
    """Convert a date to Julian day (naive midnight UTC)."""
    # Method from Astronomical Algorithms by Meeus
    y = d.year
    m = d.month
    day = d.day
    a = (14 - m) // 12
    y2 = y + 4800 - a
    m2 = m + 12*a - 3
    jd = day + ((153*m2 + 2)//5) + 365*y2 + (y2//4) - (y2//100) + (y2//400) - 32045
    return float(jd)

def _calc_solar_noon_jd(jd, longitude_deg):
    """Compute approximate solar noon (in Julian days) at the given longitude."""
    # Based on NOAA's approximation
    n = jd - 2451545.0 - (longitude_deg / 360.0)
    # Mean solar noon
    return 2451545.0 + n

def _solar_mean_anomaly(n):
    return (357.5291 + 0.98560028 * n) % 360.0

def _ecliptic_longitude(M):
    # M in degrees
    M_rad = _to_radians(M)
    C = (1.9148 * math.sin(M_rad)
         + 0.0200 * math.sin(2.0 * M_rad)
         + 0.0003 * math.sin(3.0 * M_rad))
    return (M + 102.9372 + C + 180.0) % 360.0

def _sun_declination(eclipt_long_deg):
    eclipt_long_rad = _to_radians(eclipt_long_deg)
    # Earth axial tilt ~ 23.4393°, simplified
    return _to_degrees(math.asin(math.sin(eclipt_long_rad) * math.sin(_to_radians(23.4393))))

def _hour_angle(lat_deg, decl_deg, depression):
    """
    Return hour angle in degrees for the given latitude, declination, and desired
    "depression" angle below horizon for the upper limb of the Sun.

    depression is typically 0.8333 for sunrise/sunset or 6.0 for dawn/dusk, etc.
    """
    lat_rad = _to_radians(lat_deg)
    decl_rad = _to_radians(decl_deg)
    # For sunrise, we want the sun at -depression degrees below horizon
    # The formula is cos(H) = (sin(h0) - sin(lat)*sin(dec)) / (cos(lat)*cos(dec))
    # h0 = -depression
    h0_rad = _to_radians(-depression)
    # But we want sin(h0) = sin(-depression) = - sin(depression)
    # so
    numerator = math.sin(h0_rad) - math.sin(lat_rad)*math.sin(decl_rad)
    denominator = math.cos(lat_rad)*math.cos(decl_rad)
    val = numerator / denominator
    # clamp to [-1, 1] to avoid domain errors
    val = max(min(val, 1.0), -1.0)
    return _to_degrees(math.acos(val))

def _calc_event_utc(date, latitude, longitude, depression, is_rise=True):
    """
    Calculate the UTC time (naive) for sunrise or sunset for the given date,
    latitude, longitude, and depression angle.
    This is a simplified approach to NOAA's formula.
    """
    jd = _date_to_julian_day(date)
    # approximate solar noon first
    noon_approx_jd = _calc_solar_noon_jd(jd, longitude)

    n = noon_approx_jd - 2451545.0
    M = _solar_mean_anomaly(n)
    L = _ecliptic_longitude(M)
    dec = _sun_declination(L)

    h = _hour_angle(latitude, dec, depression)
    if not is_rise:
        h = -h

    # convert hour angle to fraction of 360
    # about 1 day = 360 degrees, so each degree is 1/360 of day
    day_offset = h / 360.0

    # final JD
    event_jd = noon_approx_jd + day_offset

    # convert from JD to naive UTC datetime
    # JD reference is 4713 BC. We'll adapt the standard conversion:
    # JD 1970-01-01 is 2440587.5 => so 1 JD = 86400 seconds
    event_unix = (event_jd - 2440587.5) * 86400.0
    return dt.utcfromtimestamp(event_unix)

def _solar_noon_utc(date, latitude, longitude):
    """
    Approximate solar noon (UTC) as a naive datetime, for convenience.
    """
    jd = _date_to_julian_day(date)
    noon_approx_jd = _calc_solar_noon_jd(jd, longitude)
    # convert to dt
    event_unix = (noon_approx_jd - 2440587.5) * 86400.0
    return dt.utcfromtimestamp(event_unix)

def sun(observer, date=None, tzinfo=None):
    """
    Return a dictionary of dawn, sunrise, noon, sunset and dusk times
    for the given observer on the specified date.
    Times are returned in tzinfo time zone if provided; otherwise in UTC.
    """
    if date is None:
        date = datetime.date.today()

    lat = observer.latitude
    lon = observer.longitude

    # dawn
    dawn_utc = _calc_event_utc(date, lat, lon, CIVIL_TWILIGHT_DEGREES, True)
    # sunrise
    sunrise_utc = _calc_event_utc(date, lat, lon, SUN_APPARENT_RADIUS, True)
    # noon
    noon_utc = _solar_noon_utc(date, lat, lon)
    # sunset
    sunset_utc = _calc_event_utc(date, lat, lon, SUN_APPARENT_RADIUS, False)
    # dusk
    dusk_utc = _calc_event_utc(date, lat, lon, CIVIL_TWILIGHT_DEGREES, False)

    return {
        "dawn": _utc_to_tz(dawn_utc, tzinfo),
        "sunrise": _utc_to_tz(sunrise_utc, tzinfo),
        "noon": _utc_to_tz(noon_utc, tzinfo),
        "sunset": _utc_to_tz(sunset_utc, tzinfo),
        "dusk": _utc_to_tz(dusk_utc, tzinfo),
    }

def sunrise(observer, date=None, tzinfo=None):
    """Convenience function returning the sunrise time."""
    return sun(observer, date, tzinfo)["sunrise"]

def sunset(observer, date=None, tzinfo=None):
    """Convenience function returning the sunset time."""
    return sun(observer, date, tzinfo)["sunset"]