"""
Sun time calculations.
"""

import math
from datetime import datetime, timedelta, time
from typing import Optional, Dict, Any
import pytz

from .location import Observer


def _julian_day(date: datetime) -> float:
    """Calculate Julian Day Number."""
    a = (14 - date.month) // 12
    y = date.year + 4800 - a
    m = date.month + 12 * a - 3
    jdn = date.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return jdn + (date.hour - 12) / 24.0 + date.minute / 1440.0 + date.second / 86400.0


def _julian_centuries(jd: float) -> float:
    """Calculate Julian centuries from J2000.0."""
    return (jd - 2451545.0) / 36525.0


def _mean_solar_time(jd: float, longitude: float) -> float:
    """Calculate mean solar time."""
    return jd + longitude / 360.0


def _sun_geometric_mean_longitude(t: float) -> float:
    """Calculate sun's geometric mean longitude in degrees."""
    l0 = 280.46646 + t * (36000.76983 + t * 0.0003032)
    return l0 % 360.0


def _sun_geometric_mean_anomaly(t: float) -> float:
    """Calculate sun's geometric mean anomaly in degrees."""
    m = 357.52911 + t * (35999.05029 - t * 0.0001536)
    return m % 360.0


def _earth_orbit_eccentricity(t: float) -> float:
    """Calculate Earth's orbit eccentricity."""
    return 0.016708634 - t * (0.000042037 + t * 0.0000001267)


def _sun_equation_of_center(t: float) -> float:
    """Calculate sun's equation of center in degrees."""
    m = _sun_geometric_mean_anomaly(t)
    m_rad = math.radians(m)
    
    c = ((1.914602 - t * (0.004817 + t * 0.000014)) * math.sin(m_rad) +
         (0.019993 - t * 0.000101) * math.sin(2 * m_rad) +
         0.000029 * math.sin(3 * m_rad))
    
    return c


def _sun_true_longitude(t: float) -> float:
    """Calculate sun's true longitude in degrees."""
    l0 = _sun_geometric_mean_longitude(t)
    c = _sun_equation_of_center(t)
    return l0 + c


def _sun_apparent_longitude(t: float) -> float:
    """Calculate sun's apparent longitude in degrees."""
    true_long = _sun_true_longitude(t)
    omega = 125.04 - 1934.136 * t
    return true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))


def _mean_obliquity_of_ecliptic(t: float) -> float:
    """Calculate mean obliquity of ecliptic in degrees."""
    seconds = 21.448 - t * (4680.93 + t * (1.55 + t * (1999.25 - t * (51.38 + t * (249.67 + t * (-39.05 + t * (7.12 + t * (12.36 + t * (-1.06 + t * 0.01801))))))))))
    return 23.0 + (26.0 + seconds / 60.0) / 60.0


def _obliquity_correction(t: float) -> float:
    """Calculate corrected obliquity of ecliptic in degrees."""
    e0 = _mean_obliquity_of_ecliptic(t)
    omega = 125.04 - 1934.136 * t
    return e0 + 0.00256 * math.cos(math.radians(omega))


def _sun_right_ascension(t: float) -> float:
    """Calculate sun's right ascension in degrees."""
    elong = _sun_apparent_longitude(t)
    obliq = _obliquity_correction(t)
    
    elong_rad = math.radians(elong)
    obliq_rad = math.radians(obliq)
    
    num = math.cos(obliq_rad) * math.sin(elong_rad)
    den = math.cos(elong_rad)
    
    ra = math.degrees(math.atan2(num, den))
    return ra % 360.0


def _sun_declination(t: float) -> float:
    """Calculate sun's declination in degrees."""
    elong = _sun_apparent_longitude(t)
    obliq = _obliquity_correction(t)
    
    elong_rad = math.radians(elong)
    obliq_rad = math.radians(obliq)
    
    decl = math.degrees(math.asin(math.sin(obliq_rad) * math.sin(elong_rad)))
    return decl


def _equation_of_time(t: float) -> float:
    """Calculate equation of time in minutes."""
    epsilon = _obliquity_correction(t)
    l0 = _sun_geometric_mean_longitude(t)
    e = _earth_orbit_eccentricity(t)
    m = _sun_geometric_mean_anomaly(t)
    
    epsilon_rad = math.radians(epsilon)
    l0_rad = math.radians(l0)
    m_rad = math.radians(m)
    
    y = math.tan(epsilon_rad / 2.0)
    y = y * y
    
    sin2l0 = math.sin(2.0 * l0_rad)
    sinm = math.sin(m_rad)
    cos2l0 = math.cos(2.0 * l0_rad)
    sin4l0 = math.sin(4.0 * l0_rad)
    sin2m = math.sin(2.0 * m_rad)
    
    etime = (y * sin2l0 - 2.0 * e * sinm + 4.0 * e * y * sinm * cos2l0 -
             0.5 * y * y * sin4l0 - 1.25 * e * e * sin2m)
    
    return math.degrees(etime) * 4.0


def _hour_angle_sunrise(latitude: float, declination: float) -> float:
    """Calculate hour angle for sunrise/sunset in degrees."""
    lat_rad = math.radians(latitude)
    decl_rad = math.radians(declination)
    
    cos_h = -math.tan(lat_rad) * math.tan(decl_rad)
    
    if cos_h > 1.0:
        return float('nan')
    elif cos_h < -1.0:
        return float('nan')
    
    return math.degrees(math.acos(cos_h))


def _calc_sun_times(observer: Observer, date: datetime) -> Dict[str, Any]:
    """
    Calculate sun times for a given observer and date.
    
    Returns a dictionary with keys: 'dawn', 'sunrise', 'noon', 'sunset', 'dusk'
    All times are timezone-aware datetime objects in the observer's timezone.
    """
    # Ensure date is naive (no timezone info)
    if date.tzinfo is not None:
        date = date.replace(tzinfo=None)
    
    # Start with noon UTC
    jd = _julian_day(datetime(date.year, date.month, date.day, 12, 0, 0))
    t = _julian_centuries(jd)
    
    # Calculate equation of time and solar noon
    eot = _equation_of_time(t)
    solar_noon_minutes = 720.0 - 4.0 * observer.longitude - eot
    solar_noon_offset = solar_noon_minutes / 1440.0
    
    jd_noon = _julian_day(datetime(date.year, date.month, date.day, 12, 0, 0)) + solar_noon_offset
    t_noon = _julian_centuries(jd_noon)
    
    # Calculate declination at solar noon
    decl = _sun_declination(t_noon)
    
    # Calculate hour angles
    ha_sunrise = _hour_angle_sunrise(observer.latitude, decl)
    
    if math.isnan(ha_sunrise):
        # Sun doesn't rise or set
        if observer.latitude > 0 and decl > 0:
            # Midnight sun
            sunrise_time = datetime(date.year, date.month, date.day, 0, 0, 0)
            sunset_time = datetime(date.year, date.month, date.day, 23, 59, 59)
        elif observer.latitude < 0 and decl < 0:
            # Midnight sun
            sunrise_time = datetime(date.year, date.month, date.day, 0, 0, 0)
            sunset_time = datetime(date.year, date.month, date.day, 23, 59, 59)
        else:
            # Polar night
            sunrise_time = datetime(date.year, date.month, date.day, 12, 0, 0)
            sunset_time = datetime(date.year, date.month, date.day, 12, 0, 0)
    else:
        # Calculate sunrise and sunset
        sunrise_minutes = 720.0 - 4.0 * (observer.longitude + ha_sunrise) - eot
        sunset_minutes = 720.0 - 4.0 * (observer.longitude - ha_sunrise) - eot
        
        sunrise_offset = sunrise_minutes / 1440.0
        sunset_offset = sunset_minutes / 1440.0
        
        jd_sunrise = _julian_day(datetime(date.year, date.month, date.day, 12, 0, 0)) + sunrise_offset
        jd_sunset = _julian_day(datetime(date.year, date.month, date.day, 12, 0, 0)) + sunset_offset
        
        sunrise_time = _jd_to_datetime(jd_sunrise)
        sunset_time = _jd_to_datetime(jd_sunset)
    
    noon_time = _jd_to_datetime(jd_noon)
    
    # Calculate dawn and dusk (civil twilight: 6 degrees below horizon)
    ha_twilight = _hour_angle_for_altitude(observer.latitude, decl, -6.0)
    
    if math.isnan(ha_twilight):
        dawn_time = sunrise_time
        dusk_time = sunset_time
    else:
        dawn_minutes = 720.0 - 4.0 * (observer.longitude + ha_twilight) - eot
        dusk_minutes = 720.0 - 4.0 * (observer.longitude - ha_twilight) - eot
        
        dawn_offset = dawn_minutes / 1440.0
        dusk_offset = dusk_minutes / 1440.0
        
        jd_dawn = _julian_day(datetime(date.year, date.month, date.day, 12, 0, 0)) + dawn_offset
        jd_dusk = _julian_day(datetime(date.year, date.month, date.day, 12, 0, 0)) + dusk_offset
        
        dawn_time = _jd_to_datetime(jd_dawn)
        dusk_time = _jd_to_datetime(jd_dusk)
    
    return {
        'dawn': dawn_time,
        'sunrise': sunrise_time,
        'noon': noon_time,
        'sunset': sunset_time,
        'dusk': dusk_time,
    }


def _hour_angle_for_altitude(latitude: float, declination: float, altitude: float) -> float:
    """Calculate hour angle for a given altitude in degrees."""
    lat_rad = math.radians(latitude)
    decl_rad = math.radians(declination)
    alt_rad = math.radians(altitude)
    
    cos_h = (math.sin(alt_rad) - math.sin(lat_rad) * math.sin(decl_rad)) / (
        math.cos(lat_rad) * math.cos(decl_rad)
    )
    
    if cos_h > 1.0 or cos_h < -1.0:
        return float('nan')
    
    return math.degrees(math.acos(cos_h))


def _jd_to_datetime(jd: float) -> datetime:
    """Convert Julian Day to datetime."""
    jd = jd + 0.5
    z = int(jd)
    f = jd - z
    
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4
    
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    
    day = b - d - int(30.6001 * e)
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    
    hour = f * 24.0
    h = int(hour)
    minute = (hour - h) * 60.0
    m = int(minute)
    second = (minute - m) * 60.0
    s = int(second)
    microsecond = int((second - s) * 1000000)
    
    return datetime(year, month, day, h, m, s, microsecond)


def sun(observer: Observer, date: Optional[datetime] = None, 
        tzinfo=None) -> Dict[str, datetime]:
    """
    Calculate sun times for a given observer and date.
    
    Args:
        observer: Observer object with latitude, longitude, elevation
        date: Date to calculate for (defaults to today)
        tzinfo: Timezone for returned times (defaults to UTC)
    
    Returns:
        Dictionary with keys: 'dawn', 'sunrise', 'noon', 'sunset', 'dusk'
        All times are timezone-aware datetime objects.
    """
    if date is None:
        date = datetime.utcnow()
    
    if tzinfo is None:
        tzinfo = pytz.UTC
    
    # Ensure date is naive
    if date.tzinfo is not None:
        date = date.replace(tzinfo=None)
    
    # Calculate times in UTC
    times = _calc_sun_times(observer, date)
    
    # Convert to requested timezone
    result = {}
    for key, dt in times.items():
        if dt is not None:
            # Assume the calculated time is in UTC
            utc_dt = pytz.UTC.localize(dt)
            result[key] = utc_dt.astimezone(tzinfo)
        else:
            result[key] = None
    
    return result


def sunrise(observer: Observer, date: Optional[datetime] = None,
            tzinfo=None) -> datetime:
    """
    Calculate sunrise time for a given observer and date.
    
    Args:
        observer: Observer object with latitude, longitude, elevation
        date: Date to calculate for (defaults to today)
        tzinfo: Timezone for returned time (defaults to UTC)
    
    Returns:
        Timezone-aware datetime object for sunrise.
    """
    times = sun(observer, date, tzinfo)
    return times['sunrise']


def sunset(observer: Observer, date: Optional[datetime] = None,
           tzinfo=None) -> datetime:
    """
    Calculate sunset time for a given observer and date.
    
    Args:
        observer: Observer object with latitude, longitude, elevation
        date: Date to calculate for (defaults to today)
        tzinfo: Timezone for returned time (defaults to UTC)
    
    Returns:
        Timezone-aware datetime object for sunset.
    """
    times = sun(observer, date, tzinfo)
    return times['sunset']