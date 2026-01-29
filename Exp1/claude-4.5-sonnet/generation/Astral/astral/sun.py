"""
Solar calculations for sunrise, sunset, and related times.
"""

import math
from datetime import datetime, date, timedelta
from typing import Dict, Optional, Union
import pytz


def _to_days(dt: datetime) -> float:
    """Convert datetime to days since J2000.0."""
    j2000 = datetime(2000, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
    delta = dt - j2000
    return delta.total_seconds() / 86400.0


def _solar_mean_anomaly(n: float) -> float:
    """Calculate solar mean anomaly."""
    return (357.5291 + 0.98560028 * n) % 360


def _equation_of_center(M: float) -> float:
    """Calculate equation of center."""
    M_rad = math.radians(M)
    C = 1.9148 * math.sin(M_rad) + 0.0200 * math.sin(2 * M_rad) + 0.0003 * math.sin(3 * M_rad)
    return C


def _ecliptic_longitude(M: float, C: float) -> float:
    """Calculate ecliptic longitude."""
    return (M + C + 180 + 102.9372) % 360


def _solar_transit(Jnoon: float, M: float, L: float) -> float:
    """Calculate solar transit time."""
    M_rad = math.radians(M)
    L_rad = math.radians(L)
    return Jnoon + 0.0053 * math.sin(M_rad) - 0.0069 * math.sin(2 * L_rad)


def _declination(L: float) -> float:
    """Calculate solar declination."""
    L_rad = math.radians(L)
    sin_dec = math.sin(L_rad) * math.sin(math.radians(23.4397))
    return math.degrees(math.asin(sin_dec))


def _hour_angle(lat: float, dec: float, angle: float) -> Optional[float]:
    """Calculate hour angle for a given solar elevation angle."""
    lat_rad = math.radians(lat)
    dec_rad = math.radians(dec)
    angle_rad = math.radians(angle)
    
    cos_omega = (math.sin(angle_rad) - math.sin(lat_rad) * math.sin(dec_rad)) / (
        math.cos(lat_rad) * math.cos(dec_rad)
    )
    
    if cos_omega < -1 or cos_omega > 1:
        return None
    
    return math.degrees(math.acos(cos_omega))


def _calculate_time(
    observer,
    target_date: date,
    angle: float,
    direction: int,
    tzinfo
) -> Optional[datetime]:
    """
    Calculate time for a given solar elevation angle.
    
    Args:
        observer: Observer object with latitude and longitude
        target_date: Date for calculation
        angle: Solar elevation angle in degrees
        direction: -1 for rise, +1 for set
        tzinfo: Timezone for result
    """
    lat = observer.latitude
    lon = observer.longitude
    
    # Julian date for noon
    dt_noon = datetime(target_date.year, target_date.month, target_date.day, 12, 0, 0, tzinfo=pytz.UTC)
    n = _to_days(dt_noon)
    
    # Approximate solar noon
    Jstar = n - lon / 360.0
    
    # Solar mean anomaly
    M = _solar_mean_anomaly(Jstar)
    
    # Equation of center
    C = _equation_of_center(M)
    
    # Ecliptic longitude
    L = _ecliptic_longitude(M, C)
    
    # Solar transit
    Jtransit = _solar_transit(Jstar, M, L)
    
    # Declination
    dec = _declination(L)
    
    # Hour angle
    omega = _hour_angle(lat, dec, angle)
    
    if omega is None:
        return None
    
    # Calculate Julian date
    if direction < 0:  # Rise
        Jset_rise = Jtransit - omega / 360.0
    else:  # Set
        Jset_rise = Jtransit + omega / 360.0
    
    # Convert back to datetime
    j2000 = datetime(2000, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
    result_dt = j2000 + timedelta(days=Jset_rise)
    
    # Convert to requested timezone
    if tzinfo is not None:
        if isinstance(tzinfo, str):
            tzinfo = pytz.timezone(tzinfo)
        result_dt = result_dt.astimezone(tzinfo)
    
    return result_dt


def sunrise(
    observer,
    date: Optional[Union[datetime, date]] = None,
    tzinfo = None
) -> datetime:
    """
    Calculate sunrise time.
    
    Args:
        observer: Observer object with latitude and longitude
        date: Date for calculation (default: today)
        tzinfo: Timezone for result
    
    Returns:
        Datetime of sunrise
    """
    if date is None:
        date = datetime.now().date()
    elif isinstance(date, datetime):
        date = date.date()
    
    # Sunrise angle: -0.833 degrees (standard refraction)
    result = _calculate_time(observer, date, -0.833, -1, tzinfo)
    
    if result is None:
        raise ValueError("Sun does not rise on this date at this location")
    
    return result


def sunset(
    observer,
    date: Optional[Union[datetime, date]] = None,
    tzinfo = None
) -> datetime:
    """
    Calculate sunset time.
    
    Args:
        observer: Observer object with latitude and longitude
        date: Date for calculation (default: today)
        tzinfo: Timezone for result
    
    Returns:
        Datetime of sunset
    """
    if date is None:
        date = datetime.now().date()
    elif isinstance(date, datetime):
        date = date.date()
    
    # Sunset angle: -0.833 degrees (standard refraction)
    result = _calculate_time(observer, date, -0.833, 1, tzinfo)
    
    if result is None:
        raise ValueError("Sun does not set on this date at this location")
    
    return result


def noon(
    observer,
    date: Optional[Union[datetime, date]] = None,
    tzinfo = None
) -> datetime:
    """
    Calculate solar noon time.
    
    Args:
        observer: Observer object with latitude and longitude
        date: Date for calculation (default: today)
        tzinfo: Timezone for result
    
    Returns:
        Datetime of solar noon
    """
    if date is None:
        date = datetime.now().date()
    elif isinstance(date, datetime):
        date = date.date()
    
    lon = observer.longitude
    
    # Julian date for noon
    dt_noon = datetime(date.year, date.month, date.day, 12, 0, 0, tzinfo=pytz.UTC)
    n = _to_days(dt_noon)
    
    # Approximate solar noon
    Jstar = n - lon / 360.0
    
    # Solar mean anomaly
    M = _solar_mean_anomaly(Jstar)
    
    # Equation of center
    C = _equation_of_center(M)
    
    # Ecliptic longitude
    L = _ecliptic_longitude(M, C)
    
    # Solar transit
    Jtransit = _solar_transit(Jstar, M, L)
    
    # Convert back to datetime
    j2000 = datetime(2000, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
    result_dt = j2000 + timedelta(days=Jtransit)
    
    # Convert to requested timezone
    if tzinfo is not None:
        if isinstance(tzinfo, str):
            tzinfo = pytz.timezone(tzinfo)
        result_dt = result_dt.astimezone(tzinfo)
    
    return result_dt


def dawn(
    observer,
    date: Optional[Union[datetime, date]] = None,
    tzinfo = None
) -> datetime:
    """
    Calculate dawn time (civil twilight).
    
    Args:
        observer: Observer object with latitude and longitude
        date: Date for calculation (default: today)
        tzinfo: Timezone for result
    
    Returns:
        Datetime of dawn
    """
    if date is None:
        date = datetime.now().date()
    elif isinstance(date, datetime):
        date = date.date()
    
    # Civil dawn angle: -6 degrees
    result = _calculate_time(observer, date, -6.0, -1, tzinfo)
    
    if result is None:
        raise ValueError("Civil dawn does not occur on this date at this location")
    
    return result


def dusk(
    observer,
    date: Optional[Union[datetime, date]] = None,
    tzinfo = None
) -> datetime:
    """
    Calculate dusk time (civil twilight).
    
    Args:
        observer: Observer object with latitude and longitude
        date: Date for calculation (default: today)
        tzinfo: Timezone for result
    
    Returns:
        Datetime of dusk
    """
    if date is None:
        date = datetime.now().date()
    elif isinstance(date, datetime):
        date = date.date()
    
    # Civil dusk angle: -6 degrees
    result = _calculate_time(observer, date, -6.0, 1, tzinfo)
    
    if result is None:
        raise ValueError("Civil dusk does not occur on this date at this location")
    
    return result


def sun(
    observer,
    date: Optional[Union[datetime, date]] = None,
    tzinfo = None
) -> Dict[str, datetime]:
    """
    Calculate solar times for a given date.
    
    Args:
        observer: Observer object with latitude and longitude
        date: Date for calculation (default: today)
        tzinfo: Timezone for result
    
    Returns:
        Dictionary with keys: dawn, sunrise, noon, sunset, dusk
    """
    if date is None:
        date = datetime.now().date()
    elif isinstance(date, datetime):
        date = date.date()
    
    return {
        "dawn": dawn(observer, date, tzinfo),
        "sunrise": sunrise(observer, date, tzinfo),
        "noon": noon(observer, date, tzinfo),
        "sunset": sunset(observer, date, tzinfo),
        "dusk": dusk(observer, date, tzinfo),
    }