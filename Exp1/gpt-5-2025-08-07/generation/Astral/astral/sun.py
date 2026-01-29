import math
from datetime import datetime, date as date_cls, timedelta, timezone
from typing import Optional, Dict, Union

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover - fallback for older Python environments
    ZoneInfo = None  # type: ignore

from .location import Observer, LocationInfo


# Constants
ZENITH_OFFICIAL = 90.833  # official sunrise/sunset zenith, includes refraction
ZENITH_CIVIL = 96.0       # civil twilight dawn/dusk zenith

# Helper to convert tzinfo parameter
def _coerce_tzinfo(tzinfo: Optional[Union[str, timezone]]) -> Optional[timezone]:
    if tzinfo is None:
        return None
    if isinstance(tzinfo, timezone):
        return tzinfo
    if isinstance(tzinfo, str):
        if ZoneInfo is None:
            # Fallback: treat as UTC if zoneinfo not available
            return timezone.utc
        try:
            return ZoneInfo(tzinfo)
        except Exception:
            return timezone.utc
    # Support general tzinfo implementations (pytz, etc.)
    return tzinfo  # type: ignore


def _observer_from_any(obj: Union[Observer, LocationInfo, object]) -> Observer:
    if isinstance(obj, Observer):
        return obj
    if isinstance(obj, LocationInfo):
        return obj.observer
    # Try duck-typing
    lat = getattr(obj, "latitude", None)
    lon = getattr(obj, "longitude", None)
    ele = getattr(obj, "elevation", 0.0)
    if lat is None or lon is None:
        raise TypeError("observer must provide latitude and longitude attributes")
    return Observer(float(lat), float(lon), float(ele))


def _to_timezone(dt_utc: datetime, tzinfo: Optional[Union[str, timezone]]) -> datetime:
    tz = _coerce_tzinfo(tzinfo)
    if tz is None:
        # Default to UTC to keep times timezone-aware
        tz = timezone.utc
    return dt_utc.astimezone(tz)


def _day_of_year(d: date_cls) -> int:
    return d.timetuple().tm_yday


def _normalize_degrees(angle: float) -> float:
    """Normalize angle to [0, 360)."""
    res = angle % 360.0
    if res < 0:
        res += 360.0
    return res


def _acos_clamped(x: float) -> float:
    """Safe arccos in degrees, clamping to [-1,1]. Returns degrees."""
    x = max(-1.0, min(1.0, x))
    return math.degrees(math.acos(x))


def _calc_solar_ra_deg(true_long_deg: float) -> float:
    # Right ascension in degrees per NOAA method
    # RA = arctan(0.91764 * tan(L))
    ra_rad = math.atan(0.91764 * math.tan(math.radians(true_long_deg)))
    ra_deg = math.degrees(ra_rad)
    # Quadrant correction
    Lquadrant = (math.floor(true_long_deg / 90.0)) * 90.0
    RAquadrant = (math.floor(ra_deg / 90.0)) * 90.0
    ra_deg = ra_deg + (Lquadrant - RAquadrant)
    return ra_deg


def _sun_event_utc_hours(d: date_cls, lat_deg: float, lon_deg: float, zenith_deg: float, is_sunrise: bool) -> Optional[float]:
    """
    Compute time of sunrise/sunset-like event in UTC hours using NOAA algorithm.
    Returns UT hours for the given date or None if no event occurs.
    """
    N = _day_of_year(d)
    lngHour = lon_deg / 15.0
    approx_hour = 6.0 if is_sunrise else 18.0
    t = N + ((approx_hour - lngHour) / 24.0)

    # Sun's mean anomaly
    M = 0.9856 * t - 3.289

    # Sun's true longitude
    L = M + (1.916 * math.sin(math.radians(M))) + (0.020 * math.sin(math.radians(2 * M))) + 282.634
    L = _normalize_degrees(L)

    # Sun's right ascension
    RA_deg = _calc_solar_ra_deg(L)
    RA_hours = RA_deg / 15.0

    # Sun's declination
    sinDec = 0.39782 * math.sin(math.radians(L))
    cosDec = math.cos(math.asin(sinDec))

    # Local hour angle
    cosH = (math.cos(math.radians(zenith_deg)) - (sinDec * math.sin(math.radians(lat_deg)))) / (cosDec * math.cos(math.radians(lat_deg)))

    if cosH > 1.0:
        # Sun never rises at this location on the specified date
        return None
    if cosH < -1.0:
        # Sun never sets at this location on the specified date
        return None

    H_deg = 360.0 - _acos_clamped(cosH) if is_sunrise else _acos_clamped(cosH)
    H_hours = H_deg / 15.0

    # Local mean time of rising/setting (in hours)
    T = H_hours + RA_hours - (0.06571 * t) - 6.622

    # UT in hours
    UT = T - lngHour
    # Normalize to [0,24)
    UT = UT % 24.0
    return UT


def _calc_noon_utc_hours(d: date_cls, lat_deg: float, lon_deg: float) -> float:
    """
    Approximate solar noon (transit) using NOAA approach with hour angle = 0.
    Returns UT hours.
    """
    N = _day_of_year(d)
    lngHour = lon_deg / 15.0
    t = N + ((12.0 - lngHour) / 24.0)

    # Sun's mean anomaly
    M = 0.9856 * t - 3.289

    # Sun's true longitude
    L = M + (1.916 * math.sin(math.radians(M))) + (0.020 * math.sin(math.radians(2 * M))) + 282.634
    L = _normalize_degrees(L)

    # Right ascension
    RA_deg = _calc_solar_ra_deg(L)
    RA_hours = RA_deg / 15.0

    # Local mean time with hour angle H=0
    T = 0.0 + RA_hours - (0.06571 * t) - 6.622
    UT = (T - lngHour) % 24.0
    return UT


def _utc_hours_to_dt(d: date_cls, ut_hours: float) -> datetime:
    dt_utc = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) + timedelta(hours=ut_hours)
    return dt_utc


def sunrise(observer: Union[Observer, LocationInfo, object], date: Optional[Union[date_cls, datetime]] = None,
            tzinfo: Optional[Union[str, timezone]] = None) -> Optional[datetime]:
    obs = _observer_from_any(observer)
    d = _ensure_date(date, tzinfo, observer)
    ut = _sun_event_utc_hours(d, obs.latitude, obs.longitude, ZENITH_OFFICIAL, is_sunrise=True)
    if ut is None:
        return None
    return _to_timezone(_utc_hours_to_dt(d, ut), _resolve_tzinfo(tzinfo, observer))


def sunset(observer: Union[Observer, LocationInfo, object], date: Optional[Union[date_cls, datetime]] = None,
           tzinfo: Optional[Union[str, timezone]] = None) -> Optional[datetime]:
    obs = _observer_from_any(observer)
    d = _ensure_date(date, tzinfo, observer)
    ut = _sun_event_utc_hours(d, obs.latitude, obs.longitude, ZENITH_OFFICIAL, is_sunrise=False)
    if ut is None:
        return None
    return _to_timezone(_utc_hours_to_dt(d, ut), _resolve_tzinfo(tzinfo, observer))


def dawn(observer: Union[Observer, LocationInfo, object], date: Optional[Union[date_cls, datetime]] = None,
         tzinfo: Optional[Union[str, timezone]] = None) -> Optional[datetime]:
    obs = _observer_from_any(observer)
    d = _ensure_date(date, tzinfo, observer)
    ut = _sun_event_utc_hours(d, obs.latitude, obs.longitude, ZENITH_CIVIL, is_sunrise=True)
    if ut is None:
        return None
    return _to_timezone(_utc_hours_to_dt(d, ut), _resolve_tzinfo(tzinfo, observer))


def dusk(observer: Union[Observer, LocationInfo, object], date: Optional[Union[date_cls, datetime]] = None,
         tzinfo: Optional[Union[str, timezone]] = None) -> Optional[datetime]:
    obs = _observer_from_any(observer)
    d = _ensure_date(date, tzinfo, observer)
    ut = _sun_event_utc_hours(d, obs.latitude, obs.longitude, ZENITH_CIVIL, is_sunrise=False)
    if ut is None:
        return None
    return _to_timezone(_utc_hours_to_dt(d, ut), _resolve_tzinfo(tzinfo, observer))


def noon(observer: Union[Observer, LocationInfo, object], date: Optional[Union[date_cls, datetime]] = None,
         tzinfo: Optional[Union[str, timezone]] = None) -> datetime:
    obs = _observer_from_any(observer)
    d = _ensure_date(date, tzinfo, observer)
    # Prefer average of sunrise/sunset if available for consistency.
    sr = _sun_event_utc_hours(d, obs.latitude, obs.longitude, ZENITH_OFFICIAL, is_sunrise=True)
    ss = _sun_event_utc_hours(d, obs.latitude, obs.longitude, ZENITH_OFFICIAL, is_sunrise=False)
    if sr is not None and ss is not None:
        ut = (sr + (ss - sr) / 2.0) % 24.0
    else:
        ut = _calc_noon_utc_hours(d, obs.latitude, obs.longitude)
    return _to_timezone(_utc_hours_to_dt(d, ut), _resolve_tzinfo(tzinfo, observer))


def sun(observer: Union[Observer, LocationInfo, object], date: Optional[Union[date_cls, datetime]] = None,
        tzinfo: Optional[Union[str, timezone]] = None) -> Dict[str, Optional[datetime]]:
    """
    Returns a dictionary with keys:
      'dawn', 'sunrise', 'noon', 'sunset', 'dusk'
    Values are timezone-aware datetime objects in the requested tzinfo.
    """
    obs = _observer_from_any(observer)
    d = _ensure_date(date, tzinfo, observer)
    tz = _resolve_tzinfo(tzinfo, observer)

    dawn_dt = None
    sunrise_dt = None
    sunset_dt = None
    dusk_dt = None

    dawn_ut = _sun_event_utc_hours(d, obs.latitude, obs.longitude, ZENITH_CIVIL, is_sunrise=True)
    if dawn_ut is not None:
        dawn_dt = _to_timezone(_utc_hours_to_dt(d, dawn_ut), tz)

    sunrise_ut = _sun_event_utc_hours(d, obs.latitude, obs.longitude, ZENITH_OFFICIAL, is_sunrise=True)
    if sunrise_ut is not None:
        sunrise_dt = _to_timezone(_utc_hours_to_dt(d, sunrise_ut), tz)

    sunset_ut = _sun_event_utc_hours(d, obs.latitude, obs.longitude, ZENITH_OFFICIAL, is_sunrise=False)
    if sunset_ut is not None:
        sunset_dt = _to_timezone(_utc_hours_to_dt(d, sunset_ut), tz)

    dusk_ut = _sun_event_utc_hours(d, obs.latitude, obs.longitude, ZENITH_CIVIL, is_sunrise=False)
    if dusk_ut is not None:
        dusk_dt = _to_timezone(_utc_hours_to_dt(d, dusk_ut), tz)

    # Noon
    if sunrise_ut is not None and sunset_ut is not None:
        noon_ut = (sunrise_ut + (sunset_ut - sunrise_ut) / 2.0) % 24.0
    else:
        noon_ut = _calc_noon_utc_hours(d, obs.latitude, obs.longitude)
    noon_dt = _to_timezone(_utc_hours_to_dt(d, noon_ut), tz)

    return {
        "dawn": dawn_dt,
        "sunrise": sunrise_dt,
        "noon": noon_dt,
        "sunset": sunset_dt,
        "dusk": dusk_dt,
    }


def _resolve_tzinfo(tzinfo: Optional[Union[str, timezone]], observer: Union[Observer, LocationInfo, object]) -> timezone:
    tz = _coerce_tzinfo(tzinfo)
    if tz is not None:
        return tz
    # Try to get timezone from LocationInfo
    if isinstance(observer, LocationInfo):
        if observer.timezone and isinstance(observer.timezone, str) and ZoneInfo is not None:
            try:
                return ZoneInfo(observer.timezone)
            except Exception:
                return timezone.utc
    # fallback
    return timezone.utc


def _ensure_date(d: Optional[Union[date_cls, datetime]], tzinfo: Optional[Union[str, timezone]],
                 observer: Union[Observer, LocationInfo, object]) -> date_cls:
    """
    Ensures we have a date object. If datetime is provided, convert to given tz and take date.
    If None, derive today's date in provided tz (or observer timezone if available).
    """
    tz = _resolve_tzinfo(tzinfo, observer)
    if d is None:
        # Use current date in requested timezone for consistency
        return datetime.now(tz).date()
    if isinstance(d, datetime):
        # Convert to requested tz and take the date
        return d.astimezone(tz).date()
    return d