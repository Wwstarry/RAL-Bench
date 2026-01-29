from __future__ import annotations

import math
from datetime import date, datetime, time, timezone
from typing import Optional, Union

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


Number = Union[int, float]


def _to_radians(deg: Number) -> float:
    return float(deg) * math.pi / 180.0


def _to_degrees(rad: Number) -> float:
    return float(rad) * 180.0 / math.pi


def _normalize_degrees(deg: Number) -> float:
    x = float(deg) % 360.0
    if x < 0:
        x += 360.0
    return x


def _normalize_minutes(mins: Number) -> float:
    x = float(mins) % 1440.0
    if x < 0:
        x += 1440.0
    return x


def _coerce_tzinfo(tzinfo):
    if tzinfo is None:
        return timezone.utc
    if isinstance(tzinfo, str):
        if ZoneInfo is None:  # pragma: no cover
            raise ValueError("zoneinfo.ZoneInfo is not available on this Python")
        return ZoneInfo(tzinfo)
    return tzinfo


def _date_from_any(d, tzinfo) -> date:
    tz = _coerce_tzinfo(tzinfo)
    if d is None:
        return datetime.now(tz).date()
    if isinstance(d, datetime):
        if d.tzinfo is None:
            # Interpret naive datetimes as being in tz
            d = d.replace(tzinfo=tz)
        else:
            d = d.astimezone(tz)
        return d.date()
    if isinstance(d, date):
        return d
    raise TypeError("date must be None, datetime.date, or datetime.datetime")


def _aware_datetime_on_date(d: date, minutes: float, tzinfo) -> datetime:
    """Build an aware datetime at local tz for a date + minutes from midnight.

    minutes may be outside [0, 1440); it will be normalized to the day by modulo,
    which is consistent with NOAA-style calculations. For typical tests this
    stays within the day.
    """
    tz = _coerce_tzinfo(tzinfo)
    minutes = float(minutes)
    minutes = _normalize_minutes(minutes)
    hh = int(minutes // 60)
    mm = int(minutes % 60)
    ss = int(round((minutes - (hh * 60 + mm)) * 60))
    if ss == 60:
        ss = 0
        mm += 1
    if mm == 60:
        mm = 0
        hh += 1
    if hh == 24:
        # Normalize to start of next day; rarely needed for typical sunrise/sunset usage.
        dt = datetime.combine(d, time(0, 0, 0), tzinfo=tz) + timedelta(days=1)
        return dt
    return datetime(d.year, d.month, d.day, hh, mm, ss, tzinfo=tz)


def _validate_lat_lon(lat: float, lon: float) -> None:
    if not (-90.0 <= lat <= 90.0):
        raise ValueError("Latitude must be in the range [-90, 90]")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError("Longitude must be in the range [-180, 180]")


def _duck_observer(observer):
    try:
        lat = float(observer.latitude)
        lon = float(observer.longitude)
    except Exception as e:  # pragma: no cover
        raise TypeError("observer must have latitude and longitude attributes") from e
    elev = float(getattr(observer, "elevation", 0.0))
    _validate_lat_lon(lat, lon)
    return lat, lon, elev


def _julian_day(dt_utc: datetime) -> float:
    """Julian Day for a UTC datetime."""
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    dt_utc = dt_utc.astimezone(timezone.utc)

    y = dt_utc.year
    m = dt_utc.month
    D = dt_utc.day + (dt_utc.hour + (dt_utc.minute + (dt_utc.second + dt_utc.microsecond / 1e6) / 60.0) / 60.0) / 24.0

    if m <= 2:
        y -= 1
        m += 12
    A = y // 100
    B = 2 - A + (A // 4)
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + D + B - 1524.5
    return float(jd)


def _julian_century(jd: float) -> float:
    return (jd - 2451545.0) / 36525.0


def _geom_mean_long_sun(T: float) -> float:
    L0 = 280.46646 + T * (36000.76983 + T * 0.0003032)
    return _normalize_degrees(L0)


def _geom_mean_anom_sun(T: float) -> float:
    return 357.52911 + T * (35999.05029 - 0.0001537 * T)


def _eccent_earth_orbit(T: float) -> float:
    return 0.016708634 - T * (0.000042037 + 0.0000001267 * T)


def _sun_eq_of_center(T: float) -> float:
    M = _to_radians(_geom_mean_anom_sun(T))
    sinM = math.sin(M)
    sin2M = math.sin(2 * M)
    sin3M = math.sin(3 * M)
    C = (sinM * (1.914602 - T * (0.004817 + 0.000014 * T)) +
         sin2M * (0.019993 - 0.000101 * T) +
         sin3M * 0.000289)
    return C


def _sun_true_long(T: float) -> float:
    return _geom_mean_long_sun(T) + _sun_eq_of_center(T)


def _sun_app_long(T: float) -> float:
    omega = 125.04 - 1934.136 * T
    return _sun_true_long(T) - 0.00569 - 0.00478 * math.sin(_to_radians(omega))


def _mean_obliq_ecliptic(T: float) -> float:
    seconds = 21.448 - T * (46.8150 + T * (0.00059 - T * 0.001813))
    return 23.0 + (26.0 + (seconds / 60.0)) / 60.0


def _obliq_corr(T: float) -> float:
    e0 = _mean_obliq_ecliptic(T)
    omega = 125.04 - 1934.136 * T
    return e0 + 0.00256 * math.cos(_to_radians(omega))


def _sun_declination(T: float) -> float:
    e = _to_radians(_obliq_corr(T))
    lam = _to_radians(_sun_app_long(T))
    sint = math.sin(e) * math.sin(lam)
    return _to_degrees(math.asin(sint))


def _equation_of_time_minutes(T: float) -> float:
    epsilon = _to_radians(_obliq_corr(T))
    L0 = _to_radians(_geom_mean_long_sun(T))
    e = _eccent_earth_orbit(T)
    M = _to_radians(_geom_mean_anom_sun(T))

    y = math.tan(epsilon / 2.0)
    y *= y

    sin2L0 = math.sin(2.0 * L0)
    sinM = math.sin(M)
    cos2L0 = math.cos(2.0 * L0)
    sin4L0 = math.sin(4.0 * L0)
    sin2M = math.sin(2.0 * M)

    Etime = (y * sin2L0 -
             2.0 * e * sinM +
             4.0 * e * y * sinM * cos2L0 -
             0.5 * y * y * sin4L0 -
             1.25 * e * e * sin2M)
    return _to_degrees(Etime) * 4.0  # minutes of time


def _hour_angle_deg(latitude_deg: float, solar_dec_deg: float, solar_zenith_deg: float) -> float:
    lat = _to_radians(latitude_deg)
    sd = _to_radians(solar_dec_deg)
    zen = _to_radians(solar_zenith_deg)

    cosH = (math.cos(zen) - math.sin(lat) * math.sin(sd)) / (math.cos(lat) * math.cos(sd))
    # Numerical safety
    if cosH > 1.0:
        cosH = 1.0
    if cosH < -1.0:
        cosH = -1.0
    return _to_degrees(math.acos(cosH))