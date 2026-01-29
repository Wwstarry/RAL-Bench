# astral/sun.py

from datetime import datetime, timedelta, date, time, timezone
from math import cos, sin, tan, acos, asin, atan2, radians, degrees, floor, ceil, pi
from typing import Optional, Dict, Any

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

from .location import Observer

# Constants
J2000 = 2451545.0  # Julian date at 2000-01-01 12:00:00 UTC
DEG_PER_HOUR = 360.0 / 24.0

def _to_julian_day(dt: datetime) -> float:
    """Convert a datetime to Julian Day."""
    # Astral expects UTC
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    y = dt.year
    m = dt.month
    d = dt.day + (dt.hour + dt.minute / 60 + dt.second / 3600) / 24
    if m <= 2:
        y -= 1
        m += 12
    A = floor(y / 100)
    B = 2 - A + floor(A / 4)
    jd = floor(365.25 * (y + 4716)) + floor(30.6001 * (m + 1)) + d + B - 1524.5
    return jd

def _from_julian_day(jd: float) -> datetime:
    """Convert Julian Day to datetime (UTC)."""
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
    if E < 14:
        month = E - 1
    else:
        month = E - 13
    if month > 2:
        year = C - 4716
    else:
        year = C - 4715
    day_int = int(day)
    frac = day - day_int
    hour = int(frac * 24)
    minute = int((frac * 24 - hour) * 60)
    second = int((((frac * 24 - hour) * 60) - minute) * 60)
    return datetime(year, month, day_int, hour, minute, second, tzinfo=timezone.utc)

def _fix_hour(hour: float) -> float:
    return hour % 24.0

def _mean_solar_noon(jd: float, lw: float) -> float:
    """Mean solar noon."""
    return jd - lw / 360.0

def _solar_mean_anomaly(M: float) -> float:
    return radians(M)

def _ecliptic_longitude(M: float) -> float:
    # M in degrees
    C = (1.9148 * sin(radians(M)) +
         0.0200 * sin(radians(2 * M)) +
         0.0003 * sin(radians(3 * M)))
    P = 102.9372  # perihelion of the Earth
    return radians(M + C + P + 180.0)

def _sun_declination(L: float) -> float:
    return asin(sin(L) * sin(radians(23.44)))

def _right_ascension(L: float) -> float:
    return atan2(sin(L) * cos(radians(23.44)), cos(L))

def _sidereal_time(d: float, lw: float) -> float:
    return radians((280.16 + 360.9856235 * d) - lw)

def _azimuth(H: float, phi: float, dec: float) -> float:
    return atan2(sin(H), cos(H) * sin(phi) - tan(dec) * cos(phi))

def _altitude(H: float, phi: float, dec: float) -> float:
    return asin(sin(phi) * sin(dec) + cos(phi) * cos(dec) * cos(H))

def _julian_cycle(d: float, lw: float) -> float:
    return round(d - 0.0009 - lw / 360.0)

def _approx_transit(Ht: float, lw: float, n: float) -> float:
    return 2451545.0 + n + 0.0009 + (Ht + lw) / 360.0

def _solar_transit_j(ds: float, M: float, L: float) -> float:
    return ds + 0.0053 * sin(radians(M)) - 0.0069 * sin(2 * L)

def _hour_angle(h: float, phi: float, d: float) -> float:
    # h: altitude, phi: latitude, d: declination
    cosH = (sin(h) - sin(phi) * sin(d)) / (cos(phi) * cos(d))
    if cosH < -1.0:
        cosH = -1.0
    elif cosH > 1.0:
        cosH = 1.0
    return acos(cosH)

def _observer_elevation_correction(elevation: float) -> float:
    # Correction for observer elevation (in meters)
    # Returns the angle in degrees to subtract from the standard altitude
    # See: https://en.wikipedia.org/wiki/Sunrise_equation
    return degrees(-2.076 * (elevation ** 0.5) / 60.0)

def _sun_event_time(
    observer: Observer,
    date_: date,
    angle: float,
    tzinfo: Optional[Any],
    event: str
) -> Optional[datetime]:
    """Compute the time of a sun event (rise/set/dawn/dusk) for the observer."""
    # Algorithm based on NOAA Solar Calculator
    # https://gml.noaa.gov/grad/solcalc/solareqns.PDF
    # All angles in degrees
    lw = -observer.longitude
    phi = radians(observer.latitude)
    n = _julian_cycle(_to_julian_day(datetime(date_.year, date_.month, date_.day, 12)), lw)
    ds = _mean_solar_noon(_to_julian_day(datetime(date_.year, date_.month, date_.day, 12)), lw)
    M = (357.5291 + 0.98560028 * (ds - J2000))
    L = _ecliptic_longitude(M)
    dec = _sun_declination(L)
    Jnoon = _solar_transit_j(ds, M, L)
    # Correct for observer elevation
    h0 = angle + _observer_elevation_correction(observer.elevation)
    try:
        H = _hour_angle(radians(h0), phi, dec)
    except ValueError:
        # Sun does not rise/set on this day
        return None
    if event in ("sunrise", "dawn"):
        Jrise = Jnoon - degrees(H) / 360.0
        dt = _from_julian_day(Jrise)
    elif event in ("sunset", "dusk"):
        Jset = Jnoon + degrees(H) / 360.0
        dt = _from_julian_day(Jset)
    else:
        raise ValueError("Invalid event type")
    if tzinfo is not None:
        dt = dt.astimezone(tzinfo)
    return dt

def _get_tzinfo(tzinfo, observer):
    if tzinfo is not None:
        return tzinfo
    # Try to get timezone from observer if available
    return timezone.utc

def sun(
    observer: Observer,
    date: Optional[date] = None,
    tzinfo: Optional[Any] = None
) -> Dict[str, Optional[datetime]]:
    """Return a dict of sun events for the observer on a date."""
    if date is None:
        date = datetime.now(timezone.utc).date()
    tz = _get_tzinfo(tzinfo, observer)
    # Standard sun altitudes (degrees)
    # Astral: dawn/dusk = -6, sunrise/set = -0.833, noon = 0
    events = {}
    events["dawn"] = _sun_event_time(observer, date, -6.0, tz, "dawn")
    events["sunrise"] = _sun_event_time(observer, date, -0.833, tz, "sunrise")
    events["noon"] = _sun_noon(observer, date, tz)
    events["sunset"] = _sun_event_time(observer, date, -0.833, tz, "sunset")
    events["dusk"] = _sun_event_time(observer, date, -6.0, tz, "dusk")
    return events

def _sun_noon(observer: Observer, date_: date, tzinfo: Optional[Any]) -> datetime:
    lw = -observer.longitude
    ds = _mean_solar_noon(_to_julian_day(datetime(date_.year, date_.month, date_.day, 12)), lw)
    M = (357.5291 + 0.98560028 * (ds - J2000))
    L = _ecliptic_longitude(M)
    Jnoon = _solar_transit_j(ds, M, L)
    dt = _from_julian_day(Jnoon)
    if tzinfo is not None:
        dt = dt.astimezone(tzinfo)
    return dt

def sunrise(
    observer: Observer,
    date: Optional[date] = None,
    tzinfo: Optional[Any] = None
) -> Optional[datetime]:
    """Return the sunrise time for the observer on a date."""
    if date is None:
        date = datetime.now(timezone.utc).date()
    tz = _get_tzinfo(tzinfo, observer)
    return _sun_event_time(observer, date, -0.833, tz, "sunrise")

def sunset(
    observer: Observer,
    date: Optional[date] = None,
    tzinfo: Optional[Any] = None
) -> Optional[datetime]:
    """Return the sunset time for the observer on a date."""
    if date is None:
        date = datetime.now(timezone.utc).date()
    tz = _get_tzinfo(tzinfo, observer)
    return _sun_event_time(observer, date, -0.833, tz, "sunset")

def dawn(
    observer: Observer,
    date: Optional[date] = None,
    tzinfo: Optional[Any] = None
) -> Optional[datetime]:
    """Return the dawn time for the observer on a date."""
    if date is None:
        date = datetime.now(timezone.utc).date()
    tz = _get_tzinfo(tzinfo, observer)
    return _sun_event_time(observer, date, -6.0, tz, "dawn")

def dusk(
    observer: Observer,
    date: Optional[date] = None,
    tzinfo: Optional[Any] = None
) -> Optional[datetime]:
    """Return the dusk time for the observer on a date."""
    if date is None:
        date = datetime.now(timezone.utc).date()
    tz = _get_tzinfo(tzinfo, observer)
    return _sun_event_time(observer, date, -6.0, tz, "dusk")