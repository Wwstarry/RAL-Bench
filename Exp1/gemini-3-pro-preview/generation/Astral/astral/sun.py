import math
import datetime
from astral.observer import Observer

# Constants
_RAD = math.pi / 180.0
_DEG = 180.0 / math.pi

def _get_observer_data(observer):
    if hasattr(observer, 'latitude') and hasattr(observer, 'longitude'):
        elevation = getattr(observer, 'elevation', 0.0)
        return float(observer.latitude), float(observer.longitude), float(elevation)
    if hasattr(observer, 'observer'):
        obs = observer.observer
        return float(obs.latitude), float(obs.longitude), float(obs.elevation)
    raise TypeError("Invalid observer type")

def _julianday(dt):
    # Calculate Julian Day for a given date (at 00:00 UTC usually, or actual time)
    # For solar calculations, we often need T (Julian Centuries from J2000.0)
    # J2000.0 is JD 2451545.0
    
    # Algorithm from Meeus
    y = dt.year
    m = dt.month
    d = dt.day
    # If we have time, include it as fraction of day
    f = 0.0
    if isinstance(dt, datetime.datetime):
        f = (dt.hour + dt.minute / 60.0 + dt.second / 3600.0) / 24.0
    
    if m <= 2:
        y -= 1
        m += 12
    
    a = math.floor(y / 100)
    b = 2 - a + math.floor(a / 4)
    jd = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5 + f
    return jd

def _calculate_sun_times(latitude, longitude, elevation, date_obj, depression=0.833):
    # NOAA Solar Calculation
    # depression: degrees below horizon for the event (0.833 for sunrise/set, 6 for civil, etc)
    
    # Adjust depression for elevation
    # dip = 0.0347 * sqrt(h) degrees (approx)
    if elevation > 0:
        depression += 0.0347 * math.sqrt(elevation)

    # We calculate variables at noon UTC for the given date
    # This is an approximation suitable for sunrise/sunset within a minute or two
    
    # Ensure date_obj is a date
    if isinstance(date_obj, datetime.datetime):
        date_obj = date_obj.date()
        
    jd = _julianday(date_obj)
    t = (jd - 2451545.0) / 36525.0
    
    # Geometric Mean Longitude
    l0 = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360
    
    # Geometric Mean Anomaly
    m = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    
    # Eccentricity
    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
    
    # Equation of Center
    m_rad = math.radians(m)
    sin_m = math.sin(m_rad)
    sin_2m = math.sin(2 * m_rad)
    sin_3m = math.sin(3 * m_rad)
    c = sin_m * (1.914602 - t * (0.004817 + 0.000014 * t)) + \
        sin_2m * (0.019993 - 0.000101 * t) + \
        sin_3m * 0.000289
        
    # True Longitude
    true_long = l0 + c
    
    # Apparent Longitude
    omega = 125.04 - 1934.136 * t
    lambda_sun = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    
    # Mean Obliquity
    seconds = 21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))
    epsilon0 = 23.0 + (26.0 + (seconds / 60.0)) / 60.0
    
    # Obliquity Correction
    epsilon = epsilon0 + 0.00256 * math.cos(math.radians(omega))
    
    # Declination
    rad_epsilon = math.radians(epsilon)
    rad_lambda = math.radians(lambda_sun)
    sin_delta = math.sin(rad_epsilon) * math.sin(rad_lambda)
    delta = math.degrees(math.asin(sin_delta))
    
    # Equation of Time
    y = math.tan(rad_epsilon / 2.0) ** 2
    rad_l0 = math.radians(l0)
    
    e_time = 4.0 * math.degrees(
        y * math.sin(2 * rad_l0) - 
        2 * e * math.sin(m_rad) + 
        4 * e * y * math.sin(m_rad) * math.cos(2 * rad_l0) - 
        0.5 * y * y * math.sin(4 * rad_l0) - 
        1.25 * e * e * math.sin(2 * m_rad)
    )
    
    # Solar Noon (UTC minutes)
    # longitude is East positive. NOAA formula uses West positive for this part usually:
    # Noon = 720 - 4 * Longitude - EqTime
    # Since our Longitude is East+, we use -4 * Longitude.
    noon_min = 720.0 - 4.0 * longitude - e_time
    
    # Hour Angle
    rad_phi = math.radians(latitude)
    rad_delta = math.radians(delta)
    rad_depression = math.radians(depression) # depression is positive here (e.g. 0.833)
    
    # cos(omega) = (sin(-depression) - sin(phi)sin(delta)) / (cos(phi)cos(delta))
    # Note: depression angle is usually given as positive value below horizon.
    # So altitude is -depression.
    
    numerator = math.sin(-rad_depression) - math.sin(rad_phi) * math.sin(rad_delta)
    denominator = math.cos(rad_phi) * math.cos(rad_delta)
    
    try:
        cos_omega = numerator / denominator
    except ZeroDivisionError:
        cos_omega = 2.0 # Force error
        
    if cos_omega > 1.0:
        raise ValueError("Sun never rises")
    if cos_omega < -1.0:
        raise ValueError("Sun never sets")
        
    omega = math.degrees(math.acos(cos_omega))
    
    # Sunrise/Sunset minutes
    rise_min = noon_min - 4.0 * omega
    set_min = noon_min + 4.0 * omega
    
    return noon_min, rise_min, set_min

def _minutes_to_datetime(minutes, date_obj, tzinfo):
    # Normalize minutes (handle <0 or >1440)
    # We want the time on the specific date.
    # If minutes < 0, it technically belongs to previous day UTC, but we want to represent it relative to the date.
    # However, Astral usually returns a datetime on the requested date (or shifted if timezone implies).
    # We construct UTC datetime then convert.
    
    # Base is 00:00 UTC of the date
    base = datetime.datetime(date_obj.year, date_obj.month, date_obj.day, tzinfo=datetime.timezone.utc)
    delta = datetime.timedelta(minutes=minutes)
    dt_utc = base + delta
    
    if tzinfo:
        return dt_utc.astimezone(tzinfo)
    return dt_utc

def sun(observer, date=None, tzinfo=None):
    """
    Calculate sun times.
    
    :param observer: Observer or LocationInfo
    :param date: Date to calculate for (default today)
    :param tzinfo: Timezone to return times in.
    :return: Dictionary with keys 'dawn', 'sunrise', 'noon', 'sunset', 'dusk'
    """
    if date is None:
        date = datetime.date.today()
    
    lat, lon, elev = _get_observer_data(observer)
    
    # Noon
    # We calculate noon with 0 depression? No, noon is transit.
    # We can reuse the internal calc but ignore omega.
    # Let's just call _calculate_sun_times with 0.833 to get noon and rise/set
    noon_min, rise_min, set_min = _calculate_sun_times(lat, lon, elev, date, 0.833)
    
    # Dawn/Dusk (Civil Twilight: 6 degrees)
    _, dawn_min, dusk_min = _calculate_sun_times(lat, lon, elev, date, 6.0)
    
    res = {
        'noon': _minutes_to_datetime(noon_min, date, tzinfo),
        'sunrise': _minutes_to_datetime(rise_min, date, tzinfo),
        'sunset': _minutes_to_datetime(set_min, date, tzinfo),
        'dawn': _minutes_to_datetime(dawn_min, date, tzinfo),
        'dusk': _minutes_to_datetime(dusk_min, date, tzinfo)
    }
    return res

def sunrise(observer, date=None, tzinfo=None):
    if date is None:
        date = datetime.date.today()
    lat, lon, elev = _get_observer_data(observer)
    _, rise_min, _ = _calculate_sun_times(lat, lon, elev, date, 0.833)
    return _minutes_to_datetime(rise_min, date, tzinfo)

def sunset(observer, date=None, tzinfo=None):
    if date is None:
        date = datetime.date.today()
    lat, lon, elev = _get_observer_data(observer)
    _, _, set_min = _calculate_sun_times(lat, lon, elev, date, 0.833)
    return _minutes_to_datetime(set_min, date, tzinfo)

def noon(observer, date=None, tzinfo=None):
    if date is None:
        date = datetime.date.today()
    lat, lon, elev = _get_observer_data(observer)
    noon_min, _, _ = _calculate_sun_times(lat, lon, elev, date, 0.833)
    return _minutes_to_datetime(noon_min, date, tzinfo)

def dawn(observer, date=None, tzinfo=None, depression=6.0):
    if date is None:
        date = datetime.date.today()
    lat, lon, elev = _get_observer_data(observer)
    _, dawn_min, _ = _calculate_sun_times(lat, lon, elev, date, depression)
    return _minutes_to_datetime(dawn_min, date, tzinfo)

def dusk(observer, date=None, tzinfo=None, depression=6.0):
    if date is None:
        date = datetime.date.today()
    lat, lon, elev = _get_observer_data(observer)
    _, _, dusk_min = _calculate_sun_times(lat, lon, elev, date, depression)
    return _minutes_to_datetime(dusk_min, date, tzinfo)