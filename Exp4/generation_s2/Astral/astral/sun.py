from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date as Date, datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo

from .location import Observer


def _to_tzinfo(tz: str | tzinfo | None) -> tzinfo:
    if tz is None:
        return timezone.utc
    if isinstance(tz, str):
        return ZoneInfo(tz)
    return tz


def _is_aware(dt: datetime) -> bool:
    return dt.tzinfo is not None and dt.utcoffset() is not None


def _date_or_today(d: Date | datetime | None, tz: tzinfo) -> Date:
    if d is None:
        return datetime.now(tz).date()
    if isinstance(d, datetime):
        if d.tzinfo is None:
            return d.date()
        return d.astimezone(tz).date()
    return d


def _julian_day(dt_utc: datetime) -> float:
    # Valid for Gregorian calendar; dt_utc must be UTC.
    if dt_utc.tzinfo is None:
        raise ValueError("dt_utc must be timezone-aware")
    dt_utc = dt_utc.astimezone(timezone.utc)
    y = dt_utc.year
    m = dt_utc.month
    d = dt_utc.day + (dt_utc.hour + (dt_utc.minute + dt_utc.second / 60.0) / 60.0) / 24.0

    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5
    return jd


def _sun_geom(jd: float) -> tuple[float, float, float, float]:
    # Returns:
    # T (Julian centuries), declination rad, equation of time minutes, solar distance AU (unused)
    T = (jd - 2451545.0) / 36525.0

    # Geometric mean longitude of the sun (deg)
    L0 = (280.46646 + T * (36000.76983 + T * 0.0003032)) % 360.0
    # Geometric mean anomaly (deg)
    M = 357.52911 + T * (35999.05029 - 0.0001537 * T)
    # Eccentricity of Earth's orbit
    e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T)

    Mrad = math.radians(M)

    # Sun equation of center
    C = (
        math.sin(Mrad) * (1.914602 - T * (0.004817 + 0.000014 * T))
        + math.sin(2 * Mrad) * (0.019993 - 0.000101 * T)
        + math.sin(3 * Mrad) * 0.000289
    )

    true_long = L0 + C
    true_anom = M + C

    # Apparent longitude
    omega = 125.04 - 1934.136 * T
    lambda_sun = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))

    # Mean obliquity of ecliptic
    eps0 = 23.0 + (26.0 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60.0) / 60.0
    # Corrected obliquity
    eps = eps0 + 0.00256 * math.cos(math.radians(omega))

    # Declination
    decl = math.asin(
        math.sin(math.radians(eps)) * math.sin(math.radians(lambda_sun))
    )

    # Equation of time (minutes)
    y = math.tan(math.radians(eps) / 2.0)
    y *= y
    L0r = math.radians(L0)
    lamr = math.radians(lambda_sun)

    eq_time = 4.0 * math.degrees(
        y * math.sin(2 * L0r)
        - 2 * e * math.sin(Mrad)
        + 4 * e * y * math.sin(Mrad) * math.cos(2 * L0r)
        - 0.5 * y * y * math.sin(4 * L0r)
        - 1.25 * e * e * math.sin(2 * Mrad)
    )

    # Distance not needed for timings; kept for completeness
    R = (1.000001018 * (1 - e * e)) / (1 + e * math.cos(math.radians(true_anom)))
    return T, decl, eq_time, R


def _hour_angle(latitude_rad: float, decl_rad: float, solar_altitude_deg: float) -> float | None:
    # Returns hour angle in radians for given solar altitude.
    # If sun never reaches altitude, returns None.
    alt = math.radians(solar_altitude_deg)
    cosH = (math.sin(alt) - math.sin(latitude_rad) * math.sin(decl_rad)) / (
        math.cos(latitude_rad) * math.cos(decl_rad)
    )
    if cosH < -1.0:
        return math.pi  # always above
    if cosH > 1.0:
        return None  # always below
    return math.acos(cosH)


def _solar_noon_utc_minutes(jd: float, longitude_deg: float) -> float:
    # Approximate solar noon in minutes from 0:00 UTC
    _, _, eq_time, _ = _sun_geom(jd)
    return 720.0 - 4.0 * longitude_deg - eq_time


def _event_utc_minutes(jd: float, observer: Observer, altitude_deg: float, is_sunrise: bool) -> float | None:
    lat = math.radians(observer.latitude)
    _, decl, eq_time, _ = _sun_geom(jd)

    ha = _hour_angle(lat, decl, altitude_deg)
    if ha is None:
        return None

    ha_deg = math.degrees(ha)
    solar_noon = 720.0 - 4.0 * observer.longitude - eq_time

    if is_sunrise:
        return solar_noon - 4.0 * ha_deg
    return solar_noon + 4.0 * ha_deg


def _utc_minutes_to_datetime(d: Date, minutes: float) -> datetime:
    base = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    return base + timedelta(minutes=minutes)


def _refine_event(observer: Observer, d: Date, altitude_deg: float, is_sunrise: bool) -> datetime | None:
    # Iteratively refine using recomputed JD at approximate time.
    # Start with JD at 0:00 UTC, then refine twice.
    jd0 = _julian_day(datetime(d.year, d.month, d.day, tzinfo=timezone.utc))
    m = _event_utc_minutes(jd0, observer, altitude_deg, is_sunrise)
    if m is None:
        return None
    dt = _utc_minutes_to_datetime(d, m)

    for _ in range(2):
        jd = _julian_day(dt)
        m2 = _event_utc_minutes(jd, observer, altitude_deg, is_sunrise)
        if m2 is None:
            return None
        dt = _utc_minutes_to_datetime(d, m2)
    return dt


def _sunrise_sunset_altitude(observer: Observer) -> float:
    # Standard refraction + solar radius adjustment; small elevation effect.
    # Common NOAA approximation: -0.833 degrees at sea level.
    # Include elevation dip: approx 0.0347*sqrt(h) degrees (h meters)
    dip = 0.0347 * math.sqrt(max(observer.elevation, 0.0))
    return -0.833 - dip


def _ensure_datetime_tz(dt_utc: datetime, tz: tzinfo) -> datetime:
    if not _is_aware(dt_utc):
        raise ValueError("Internal datetime must be timezone-aware")
    return dt_utc.astimezone(tz)


def sunrise(observer: Observer, date: Date | datetime | None = None, tzinfo: str | tzinfo | None = None) -> datetime:
    tz = _to_tzinfo(tzinfo)
    d = _date_or_today(date, tz)
    alt = _sunrise_sunset_altitude(observer)
    dt = _refine_event(observer, d, alt, True)
    if dt is None:
        raise ValueError("Sun never rises on this date at this location")
    return _ensure_datetime_tz(dt, tz)


def sunset(observer: Observer, date: Date | datetime | None = None, tzinfo: str | tzinfo | None = None) -> datetime:
    tz = _to_tzinfo(tzinfo)
    d = _date_or_today(date, tz)
    alt = _sunrise_sunset_altitude(observer)
    dt = _refine_event(observer, d, alt, False)
    if dt is None:
        raise ValueError("Sun never sets on this date at this location")
    return _ensure_datetime_tz(dt, tz)


def noon(observer: Observer, date: Date | datetime | None = None, tzinfo: str | tzinfo | None = None) -> datetime:
    tz = _to_tzinfo(tzinfo)
    d = _date_or_today(date, tz)
    jd0 = _julian_day(datetime(d.year, d.month, d.day, tzinfo=timezone.utc))
    m = _solar_noon_utc_minutes(jd0, observer.longitude)
    dt = _utc_minutes_to_datetime(d, m)
    # refine once
    jd = _julian_day(dt)
    m2 = _solar_noon_utc_minutes(jd, observer.longitude)
    dt = _utc_minutes_to_datetime(d, m2)
    return _ensure_datetime_tz(dt, tz)


def dawn(
    observer: Observer,
    date: Date | datetime | None = None,
    tzinfo: str | tzinfo | None = None,
    depression: float = 6.0,
) -> datetime:
    tz = _to_tzinfo(tzinfo)
    d = _date_or_today(date, tz)
    dt = _refine_event(observer, d, -abs(depression), True)
    if dt is None:
        raise ValueError("Dawn does not occur on this date at this location")
    return _ensure_datetime_tz(dt, tz)


def dusk(
    observer: Observer,
    date: Date | datetime | None = None,
    tzinfo: str | tzinfo | None = None,
    depression: float = 6.0,
) -> datetime:
    tz = _to_tzinfo(tzinfo)
    d = _date_or_today(date, tz)
    dt = _refine_event(observer, d, -abs(depression), False)
    if dt is None:
        raise ValueError("Dusk does not occur on this date at this location")
    return _ensure_datetime_tz(dt, tz)


def sun(
    observer: Observer,
    date: Date | datetime | None = None,
    tzinfo: str | tzinfo | None = None,
    dawn_dusk_depression: float = 6.0,
) -> dict[str, datetime]:
    tz = _to_tzinfo(tzinfo)
    d = _date_or_today(date, tz)

    sr = sunrise(observer, d, tz)
    ss = sunset(observer, d, tz)
    n = noon(observer, d, tz)
    da = dawn(observer, d, tz, depression=dawn_dusk_depression)
    du = dusk(observer, d, tz, depression=dawn_dusk_depression)

    return {
        "dawn": da,
        "sunrise": sr,
        "noon": n,
        "sunset": ss,
        "dusk": du,
    }