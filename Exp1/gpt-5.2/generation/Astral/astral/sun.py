from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date as _date, datetime, time, timedelta, timezone, tzinfo
from typing import Dict, Optional, Union

from .location import Observer

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


def _as_date(d: Optional[Union[_date, datetime]]) -> _date:
    if d is None:
        return datetime.now().date()
    if isinstance(d, datetime):
        return d.date()
    return d


def _get_tz(tz: Optional[Union[str, tzinfo]]) -> tzinfo:
    if tz is None:
        return timezone.utc
    if isinstance(tz, str):
        if ZoneInfo is None:
            return timezone.utc
        try:
            return ZoneInfo(tz)
        except Exception:
            return timezone.utc
    return tz


def _to_julian_day(dt_utc: datetime) -> float:
    # dt_utc must be timezone-aware UTC
    if dt_utc.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
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


def _from_julian_day(jd: float) -> datetime:
    # Returns UTC aware datetime
    jd += 0.5
    Z = int(jd)
    F = jd - Z
    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - alpha // 4
    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)
    day = B - D - int(30.6001 * E) + F
    month = E - 1 if E < 14 else E - 13
    year = C - 4716 if month > 2 else C - 4715

    day_int = int(day)
    frac = day - day_int
    seconds = frac * 86400.0
    hour = int(seconds // 3600)
    seconds -= hour * 3600
    minute = int(seconds // 60)
    seconds -= minute * 60
    sec = int(seconds)
    micro = int(round((seconds - sec) * 1e6))
    if micro >= 1000000:
        micro -= 1000000
        sec += 1
    if sec >= 60:
        sec -= 60
        minute += 1
    if minute >= 60:
        minute -= 60
        hour += 1
    return datetime(year, month, day_int, hour, minute, sec, micro, tzinfo=timezone.utc)


def _julian_century(jd: float) -> float:
    return (jd - 2451545.0) / 36525.0


def _geom_mean_long_sun(T: float) -> float:
    L0 = 280.46646 + T * (36000.76983 + 0.0003032 * T)
    return L0 % 360.0


def _geom_mean_anom_sun(T: float) -> float:
    return 357.52911 + T * (35999.05029 - 0.0001537 * T)


def _eccent_earth_orbit(T: float) -> float:
    return 0.016708634 - T * (0.000042037 + 0.0000001267 * T)


def _sun_eq_of_center(T: float, M: float) -> float:
    Mrad = math.radians(M)
    return (
        math.sin(Mrad) * (1.914602 - T * (0.004817 + 0.000014 * T))
        + math.sin(2 * Mrad) * (0.019993 - 0.000101 * T)
        + math.sin(3 * Mrad) * 0.000289
    )


def _sun_true_long(L0: float, C: float) -> float:
    return L0 + C


def _sun_apparent_long(T: float, true_long: float) -> float:
    omega = 125.04 - 1934.136 * T
    return true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))


def _mean_obliq_ecliptic(T: float) -> float:
    seconds = 21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))
    return 23.0 + (26.0 + (seconds / 60.0)) / 60.0


def _obliq_corr(T: float, eps0: float) -> float:
    omega = 125.04 - 1934.136 * T
    return eps0 + 0.00256 * math.cos(math.radians(omega))


def _sun_declination(eps: float, lam: float) -> float:
    return math.degrees(
        math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(lam)))
    )


def _equation_of_time(T: float, eps: float, L0: float, e: float, M: float) -> float:
    y = math.tan(math.radians(eps) / 2.0)
    y *= y
    sin2L0 = math.sin(2.0 * math.radians(L0))
    sinM = math.sin(math.radians(M))
    cos2L0 = math.cos(2.0 * math.radians(L0))
    sin4L0 = math.sin(4.0 * math.radians(L0))
    sin2M = math.sin(2.0 * math.radians(M))
    Etime = (
        y * sin2L0
        - 2.0 * e * sinM
        + 4.0 * e * y * sinM * cos2L0
        - 0.5 * y * y * sin4L0
        - 1.25 * e * e * sin2M
    )
    return math.degrees(Etime) * 4.0  # minutes of time


def _hour_angle_sunrise(lat: float, solar_dec: float, zenith: float) -> float:
    lat_rad = math.radians(lat)
    sd_rad = math.radians(solar_dec)
    cos_ha = (
        math.cos(math.radians(zenith)) - math.sin(lat_rad) * math.sin(sd_rad)
    ) / (math.cos(lat_rad) * math.cos(sd_rad))

    if cos_ha > 1.0:
        return float("nan")  # sun never rises
    if cos_ha < -1.0:
        return float("nan")  # sun never sets
    return math.degrees(math.acos(cos_ha))


def _solar_noon_utc(jd: float, longitude: float) -> float:
    T = _julian_century(jd)
    L0 = _geom_mean_long_sun(T)
    M = _geom_mean_anom_sun(T)
    e = _eccent_earth_orbit(T)
    eps0 = _mean_obliq_ecliptic(T)
    eps = _obliq_corr(T, eps0)
    eqtime = _equation_of_time(T, eps, L0, e, M)
    sol_noon_utc_min = 720.0 - (4.0 * longitude) - eqtime
    return sol_noon_utc_min


def _sun_event_utc(date_: _date, observer: Observer, zenith: float, is_rise: bool) -> Optional[datetime]:
    # Uses NOAA algorithm. Returns UTC datetime or None for polar day/night.
    # Start with approximate using solar noon.
    dt0 = datetime(date_.year, date_.month, date_.day, 0, 0, tzinfo=timezone.utc)
    jd = _to_julian_day(dt0)
    noon_min = _solar_noon_utc(jd, observer.longitude)

    # First pass: compute declination at solar noon
    jd_noon = jd + noon_min / 1440.0
    T = _julian_century(jd_noon)
    L0 = _geom_mean_long_sun(T)
    M = _geom_mean_anom_sun(T)
    C = _sun_eq_of_center(T, M)
    true_long = _sun_true_long(L0, C)
    lam = _sun_apparent_long(T, true_long)
    eps0 = _mean_obliq_ecliptic(T)
    eps = _obliq_corr(T, eps0)
    solar_dec = _sun_declination(eps, lam)
    ha = _hour_angle_sunrise(observer.latitude, solar_dec, zenith)
    if math.isnan(ha):
        return None

    delta = ha * 4.0  # minutes
    event_min = noon_min - delta if is_rise else noon_min + delta

    # Second pass: recompute with updated time
    jd_event = jd + event_min / 1440.0
    T2 = _julian_century(jd_event)
    L02 = _geom_mean_long_sun(T2)
    M2 = _geom_mean_anom_sun(T2)
    e2 = _eccent_earth_orbit(T2)
    C2 = _sun_eq_of_center(T2, M2)
    true_long2 = _sun_true_long(L02, C2)
    lam2 = _sun_apparent_long(T2, true_long2)
    eps02 = _mean_obliq_ecliptic(T2)
    eps2 = _obliq_corr(T2, eps02)
    solar_dec2 = _sun_declination(eps2, lam2)
    eqtime2 = _equation_of_time(T2, eps2, L02, e2, M2)
    ha2 = _hour_angle_sunrise(observer.latitude, solar_dec2, zenith)
    if math.isnan(ha2):
        return None
    delta2 = ha2 * 4.0
    noon_min2 = 720.0 - (4.0 * observer.longitude) - eqtime2
    event_min2 = noon_min2 - delta2 if is_rise else noon_min2 + delta2

    return dt0 + timedelta(minutes=event_min2)


def _solar_noon_local(date_: _date, observer: Observer, tz: tzinfo) -> datetime:
    dt0 = datetime(date_.year, date_.month, date_.day, 0, 0, tzinfo=timezone.utc)
    jd = _to_julian_day(dt0)
    noon_min = _solar_noon_utc(jd, observer.longitude)
    noon_utc = dt0 + timedelta(minutes=noon_min)
    return noon_utc.astimezone(tz)


def dawn(observer: Observer, date: Optional[Union[_date, datetime]] = None, tzinfo: Optional[Union[str, tzinfo]] = None) -> datetime:
    tz = _get_tz(tzinfo)
    d = _as_date(date)
    # Civil dawn: sun at -6 degrees => zenith 96
    dt_utc = _sun_event_utc(d, observer, zenith=96.0, is_rise=True)
    if dt_utc is None:
        raise ValueError("Sun never rises/sets for this location and date")
    return dt_utc.astimezone(tz)


def dusk(observer: Observer, date: Optional[Union[_date, datetime]] = None, tzinfo: Optional[Union[str, tzinfo]] = None) -> datetime:
    tz = _get_tz(tzinfo)
    d = _as_date(date)
    dt_utc = _sun_event_utc(d, observer, zenith=96.0, is_rise=False)
    if dt_utc is None:
        raise ValueError("Sun never rises/sets for this location and date")
    return dt_utc.astimezone(tz)


def sunrise(observer: Observer, date: Optional[Union[_date, datetime]] = None, tzinfo: Optional[Union[str, tzinfo]] = None) -> datetime:
    tz = _get_tz(tzinfo)
    d = _as_date(date)
    # Official sunrise: 90.833 degrees includes refraction + solar radius
    dt_utc = _sun_event_utc(d, observer, zenith=90.833, is_rise=True)
    if dt_utc is None:
        raise ValueError("Sun never rises for this location and date")
    return dt_utc.astimezone(tz)


def sunset(observer: Observer, date: Optional[Union[_date, datetime]] = None, tzinfo: Optional[Union[str, tzinfo]] = None) -> datetime:
    tz = _get_tz(tzinfo)
    d = _as_date(date)
    dt_utc = _sun_event_utc(d, observer, zenith=90.833, is_rise=False)
    if dt_utc is None:
        raise ValueError("Sun never sets for this location and date")
    return dt_utc.astimezone(tz)


def noon(observer: Observer, date: Optional[Union[_date, datetime]] = None, tzinfo: Optional[Union[str, tzinfo]] = None) -> datetime:
    tz = _get_tz(tzinfo)
    d = _as_date(date)
    return _solar_noon_local(d, observer, tz)


def sun(
    observer: Observer,
    date: Optional[Union[_date, datetime]] = None,
    tzinfo: Optional[Union[str, tzinfo]] = None,
) -> Dict[str, datetime]:
    tz = _get_tz(tzinfo)
    d = _as_date(date)
    sr = sunrise(observer, d, tz)
    ss = sunset(observer, d, tz)
    dn = dawn(observer, d, tz)
    dk = dusk(observer, d, tz)
    nn = noon(observer, d, tz)
    return {
        "dawn": dn,
        "sunrise": sr,
        "noon": nn,
        "sunset": ss,
        "dusk": dk,
    }