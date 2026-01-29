"""Sun position and time calculations."""
import math
import datetime
from typing import Optional, Tuple, Dict, Any, Union
import pytz

# Astronomical constants
RAD2DEG = 180.0 / math.pi
DEG2RAD = math.pi / 180.0

def _julian_day(dt: datetime.datetime) -> float:
    """Calculate Julian day from datetime."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(pytz.UTC).replace(tzinfo=None)
    
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    
    jdn = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    jd = jdn + (dt.hour - 12) / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0
    
    return jd

def _julian_century(jd: float) -> float:
    """Calculate Julian century from Julian day."""
    return (jd - 2451545.0) / 36525.0

def _mean_obliquity_of_ecliptic(t: float) -> float:
    """Calculate mean obliquity of the ecliptic."""
    seconds = 21.448 - t * (46.8150 + t * (0.00059 - t * 0.001813))
    return 23.0 + (26.0 + (seconds / 60.0)) / 60.0

def _obliquity_correction(t: float) -> float:
    """Calculate corrected obliquity."""
    e0 = _mean_obliquity_of_ecliptic(t)
    omega = 125.04 - 1934.136 * t
    return e0 + 0.00256 * math.cos(omega * DEG2RAD)

def _geom_mean_long_sun(t: float) -> float:
    """Calculate geometric mean longitude of the sun."""
    l0 = 280.46646 + t * (36000.76983 + t * 0.0003032)
    return l0 % 360.0

def _geom_mean_anomaly_sun(t: float) -> float:
    """Calculate geometric mean anomaly of the sun."""
    return 357.52911 + t * (35999.05029 - 0.0001537 * t)

def _eccentricity_earth_orbit(t: float) -> float:
    """Calculate eccentricity of earth's orbit."""
    return 0.016708634 - t * (0.000042037 + 0.0000001267 * t)

def _sun_eq_of_center(t: float) -> float:
    """Calculate sun's equation of center."""
    m = _geom_mean_anomaly_sun(t) * DEG2RAD
    mrad = m
    sinm = math.sin(mrad)
    sin2m = math.sin(2 * mrad)
    sin3m = math.sin(3 * mrad)
    return sinm * (1.914602 - t * (0.004817 + 0.000014 * t)) + sin2m * (0.019993 - 0.000101 * t) + sin3m * 0.000289

def _sun_true_long(t: float) -> float:
    """Calculate sun's true longitude."""
    l0 = _geom_mean_long_sun(t)
    c = _sun_eq_of_center(t)
    return l0 + c

def _sun_true_anomaly(t: float) -> float:
    """Calculate sun's true anomaly."""
    m = _geom_mean_anomaly_sun(t)
    c = _sun_eq_of_center(t)
    return m + c

def _sun_rad_vector(t: float) -> float:
    """Calculate sun's radius vector."""
    v = _sun_true_anomaly(t) * DEG2RAD
    e = _eccentricity_earth_orbit(t)
    return (1.000001018 * (1 - e * e)) / (1 + e * math.cos(v))

def _sun_apparent_long(t: float) -> float:
    """Calculate sun's apparent longitude."""
    o = _sun_true_long(t)
    omega = 125.04 - 1934.136 * t
    return o - 0.00569 - 0.00478 * math.sin(omega * DEG2RAD)

def _mean_obliquity_of_ecliptic(t: float) -> float:
    """Calculate mean obliquity of the ecliptic."""
    seconds = 21.448 - t * (46.8150 + t * (0.00059 - t * 0.001813))
    return 23.0 + (26.0 + (seconds / 60.0)) / 60.0

def _obliquity_correction(t: float) -> float:
    """Calculate corrected obliquity."""
    e0 = _mean_obliquity_of_ecliptic(t)
    omega = 125.04 - 1934.136 * t
    return e0 + 0.00256 * math.cos(omega * DEG2RAD)

def _sun_right_ascension(t: float) -> float:
    """Calculate sun's right ascension."""
    o = _sun_apparent_long(t) * DEG2RAD
    e = _obliquity_correction(t) * DEG2RAD
    tananum = math.cos(e) * math.sin(o)
    tanadenom = math.cos(o)
    alpha = math.atan2(tananum, tanadenom)
    return alpha * RAD2DEG

def _sun_declination(t: float) -> float:
    """Calculate sun's declination."""
    e = _obliquity_correction(t) * DEG2RAD
    lambda_ = _sun_apparent_long(t) * DEG2RAD
    sint = math.sin(e) * math.sin(lambda_)
    return math.asin(sint) * RAD2DEG

def _equation_of_time(t: float) -> float:
    """Calculate equation of time."""
    epsilon = _obliquity_correction(t) * DEG2RAD
    l0 = _geom_mean_long_sun(t) * DEG2RAD
    e = _eccentricity_earth_orbit(t)
    m = _geom_mean_anomaly_sun(t) * DEG2RAD
    
    y = math.tan(epsilon / 2.0)
    y *= y
    
    sin2l0 = math.sin(2.0 * l0)
    sinm = math.sin(m)
    cos2l0 = math.cos(2.0 * l0)
    sin4l0 = math.sin(4.0 * l0)
    sin2m = math.sin(2.0 * m)
    
    etime = y * sin2l0 - 2.0 * e * sinm + 4.0 * e * y * sinm * cos2l0 - 0.5 * y * y * sin4l0 - 1.25 * e * e * sin2m
    return etime * RAD2DEG * 4.0

def _hour_angle(latitude: float, declination: float, zenith: float = 90.833) -> float:
    """Calculate hour angle for given latitude, declination and zenith."""
    lat_rad = latitude * DEG2RAD
    dec_rad = declination * DEG2RAD
    zenith_rad = zenith * DEG2RAD
    
    cos_ha = (math.cos(zenith_rad) - math.sin(lat_rad) * math.sin(dec_rad)) / (math.cos(lat_rad) * math.cos(dec_rad))
    
    if cos_ha > 1.0:
        return float('inf')  # Sun never rises
    if cos_ha < -1.0:
        return float('-inf')  # Sun never sets
    
    ha = math.acos(cos_ha) * RAD2DEG
    return ha

def _sunrise_sunset_time(
    observer: Tuple[float, float, float], 
    date: Optional[datetime.date] = None,
    tzinfo: Optional[datetime.tzinfo] = None,
    zenith: float = 90.833
) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
    """Calculate sunrise and sunset times."""
    if date is None:
        date = datetime.date.today()
    
    if tzinfo is None:
        tzinfo = pytz.UTC
    
    latitude, longitude, elevation = observer
    
    # Convert date to noon in the target timezone
    noon_dt = tzinfo.localize(datetime.datetime(date.year, date.month, date.day, 12, 0, 0))
    
    jd = _julian_day(noon_dt)
    t = _julian_century(jd)
    
    eq_time = _equation_of_time(t)
    solar_dec = _sun_declination(t)
    
    hour_angle = _hour_angle(latitude, solar_dec, zenith)
    
    if hour_angle == float('inf'):
        return None, None  # Sun never rises
    if hour_angle == float('-inf'):
        return None, None  # Sun never sets
    
    # Calculate sunrise and sunset times
    ha = hour_angle / 15.0  # Convert to hours
    
    # Time from noon to sunrise/sunset
    delta = ha * 60.0  # Convert to minutes
    
    # Adjust for equation of time and longitude
    eq_time_minutes = eq_time * 4.0  # Convert to minutes
    longitude_offset = longitude / 15.0 * 60.0  # Convert to minutes
    
    total_offset = eq_time_minutes - longitude_offset
    
    sunrise_minutes = 720.0 - delta - total_offset
    sunset_minutes = 720.0 + delta - total_offset
    
    # Convert minutes to time
    sunrise_time = _minutes_to_time(sunrise_minutes)
    sunset_time = _minutes_to_time(sunset_minutes)
    
    # Create datetime objects
    sunrise_dt = tzinfo.localize(datetime.datetime(
        date.year, date.month, date.day, 
        sunrise_time[0], sunrise_time[1], int(sunrise_time[2])
    ))
    sunset_dt = tzinfo.localize(datetime.datetime(
        date.year, date.month, date.day, 
        sunset_time[0], sunset_time[1], int(sunset_time[2])
    ))
    
    return sunrise_dt, sunset_dt

def _minutes_to_time(minutes: float) -> Tuple[int, int, float]:
    """Convert minutes since midnight to (hour, minute, second)."""
    hours = minutes / 60.0
    hour = int(hours)
    fractional_hour = hours - hour
    minutes_remaining = fractional_hour * 60.0
    minute = int(minutes_remaining)
    seconds = (minutes_remaining - minute) * 60.0
    return hour, minute, seconds

def _solar_noon(observer: Tuple[float, float, float], date: Optional[datetime.date] = None,
               tzinfo: Optional[datetime.tzinfo] = None) -> datetime.datetime:
    """Calculate solar noon time."""
    if date is None:
        date = datetime.date.today()
    
    if tzinfo is None:
        tzinfo = pytz.UTC
    
    latitude, longitude, elevation = observer
    
    # Convert date to noon in the target timezone
    noon_dt = tzinfo.localize(datetime.datetime(date.year, date.month, date.day, 12, 0, 0))
    
    jd = _julian_day(noon_dt)
    t = _julian_century(jd)
    
    eq_time = _equation_of_time(t)
    
    # Adjust for equation of time and longitude
    eq_time_minutes = eq_time * 4.0  # Convert to minutes
    longitude_offset = longitude / 15.0 * 60.0  # Convert to minutes
    
    total_offset = eq_time_minutes - longitude_offset
    
    solar_noon_minutes = 720.0 - total_offset  # Noon is at 720 minutes
    
    solar_noon_time = _minutes_to_time(solar_noon_minutes)
    
    return tzinfo.localize(datetime.datetime(
        date.year, date.month, date.day, 
        solar_noon_time[0], solar_noon_time[1], int(solar_noon_time[2])
    ))

def sun(observer: Tuple[float, float, float], date: Optional[datetime.date] = None,
        tzinfo: Optional[datetime.tzinfo] = None) -> Dict[str, datetime.datetime]:
    """Calculate all sun events for a given date and observer."""
    if date is None:
        date = datetime.date.today()
    
    if tzinfo is None:
        tzinfo = pytz.UTC
    
    # Calculate dawn (civil twilight)
    dawn, _ = _sunrise_sunset_time(observer, date, tzinfo, 96.0)
    
    # Calculate sunrise/sunset
    sunrise, sunset = _sunrise_sunset_time(observer, date, tzinfo, 90.833)
    
    # Calculate noon
    noon = _solar_noon(observer, date, tzinfo)
    
    # Calculate dusk (civil twilight)
    _, dusk = _sunrise_sunset_time(observer, date, tzinfo, 96.0)
    
    return {
        'dawn': dawn,
        'sunrise': sunrise,
        'noon': noon,
        'sunset': sunset,
        'dusk': dusk
    }

def sunrise(observer: Tuple[float, float, float], date: Optional[datetime.date] = None,
           tzinfo: Optional[datetime.tzinfo] = None) -> Optional[datetime.datetime]:
    """Calculate sunrise time."""
    sunrise_time, _ = _sunrise_sunset_time(observer, date, tzinfo)
    return sunrise_time

def sunset(observer: Tuple[float, float, float], date: Optional[datetime.date] = None,
          tzinfo: Optional[datetime.tzinfo] = None) -> Optional[datetime.datetime]:
    """Calculate sunset time."""
    _, sunset_time = _sunrise_sunset_time(observer, date, tzinfo)
    return sunset_time

def dawn(observer: Tuple[float, float, float], date: Optional[datetime.date] = None,
        tzinfo: Optional[datetime.tzinfo] = None) -> Optional[datetime.datetime]:
    """Calculate dawn time (civil twilight)."""
    dawn_time, _ = _sunrise_sunset_time(observer, date, tzinfo, 96.0)
    return dawn_time

def dusk(observer: Tuple[float, float, float], date: Optional[datetime.date] = None,
        tzinfo: Optional[datetime.tzinfo] = None) -> Optional[datetime.datetime]:
    """Calculate dusk time (civil twilight)."""
    _, dusk_time = _sunrise_sunset_time(observer, date, tzinfo, 96.0)
    return dusk_time

def noon(observer: Tuple[float, float, float], date: Optional[datetime.date] = None,
        tzinfo: Optional[datetime.tzinfo] = None) -> datetime.datetime:
    """Calculate solar noon time."""
    return _solar_noon(observer, date, tzinfo)