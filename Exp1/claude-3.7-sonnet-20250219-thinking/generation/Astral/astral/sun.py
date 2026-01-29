import datetime
import math

def _adjust_to_horizon(elevation):
    """Adjusts sun's apparent radius and atmospheric refraction."""
    return -0.83 - 0.0347 * math.sqrt(max(0, elevation))

def _to_julian(date):
    """Convert a datetime object to Julian date."""
    if isinstance(date, datetime.datetime):
        date_with_time = date
    else:
        date_with_time = datetime.datetime.combine(date, datetime.time())
        
    a = (14 - date_with_time.month) // 12
    y = date_with_time.year + 4800 - a
    m = date_with_time.month + 12 * a - 3
    
    jd = date_with_time.day + ((153 * m + 2) // 5) + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    
    hour = date_with_time.hour + date_with_time.minute / 60.0 + date_with_time.second / 3600.0
    jd += (hour - 12) / 24.0
    
    return jd

def _calculate_position(jd):
    """Calculate the position of the Sun for a given Julian date."""
    # Time in Julian centuries from J2000.0
    t = (jd - 2451545.0) / 36525.0
    
    # Mean longitude of the Sun
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t**2
    l0 = l0 % 360
    
    # Mean anomaly of the Sun
    m = 357.52911 + 35999.05029 * t - 0.0001537 * t**2
    m = m % 360
    m_rad = math.radians(m)
    
    # Equation of center for the Sun
    c = (1.914602 - 0.004817 * t - 0.000014 * t**2) * math.sin(m_rad)
    c += (0.019993 - 0.000101 * t) * math.sin(2 * m_rad)
    c += 0.000289 * math.sin(3 * m_rad)
    
    # True longitude of the Sun
    true_long = l0 + c
    true_long_rad = math.radians(true_long)
    
    # Obliquity of the ecliptic
    obliq = 23.439291 - 0.0130042 * t - 1.64e-7 * t**2 + 5.04e-7 * t**3
    obliq_rad = math.radians(obliq)
    
    # Right ascension and declination
    ra = math.degrees(math.atan2(math.cos(obliq_rad) * math.sin(true_long_rad), math.cos(true_long_rad)))
    ra = ra % 360
    
    dec = math.degrees(math.asin(math.sin(obliq_rad) * math.sin(true_long_rad)))
    
    return ra, dec

def _calculate_sunrise_sunset(observer, date, tzinfo, zenith):
    """Calculate sunrise and sunset times for the given observer and date."""
    latitude = math.radians(observer.latitude)
    
    # Get the Julian date for the specified date at midnight UTC
    if isinstance(date, datetime.datetime):
        base_date = date.date()
    else:
        base_date = date
    
    jd = _to_julian(base_date)
    
    # Calculate the Sun's position at the given Julian date
    n0 = jd - 2451545.0
    longitude = -observer.longitude / 360.0
    
    # Calculate solar noon
    n = n0 - longitude
    
    # Mean solar noon
    j_transit = 2451545.0 + n
    
    # Solar mean anomaly
    M = (357.5291 + 0.98560028 * n) % 360
    M_rad = math.radians(M)
    
    # Equation of center
    C = 1.9148 * math.sin(M_rad) + 0.0200 * math.sin(2 * M_rad) + 0.0003 * math.sin(3 * M_rad)
    
    # Ecliptic longitude
    L = (M + 102.9372 + C + 180) % 360
    L_rad = math.radians(L)
    
    # Solar transit
    j_transit = j_transit + 0.0053 * math.sin(M_rad) - 0.0069 * math.sin(2 * L_rad)
    
    # Declination of the Sun
    sin_dec = math.sin(L_rad) * math.sin(math.radians(23.44))
    dec = math.asin(sin_dec)
    
    # Hour angle
    cos_hour_angle = (math.sin(math.radians(zenith)) - math.sin(latitude) * math.sin(dec)) / \
                    (math.cos(latitude) * math.cos(dec))
                    
    # Handle no sunrise/sunset case
    if cos_hour_angle > 1:
        return None, None  # Sun never rises
    if cos_hour_angle < -1:
        return None, None  # Sun never sets
    
    # Calculate hour angle in degrees
    hour_angle = math.degrees(math.acos(cos_hour_angle))
    
    # Calculate Julian dates for sunrise and sunset
    j_rise = j_transit - hour_angle / 360.0
    j_set = j_transit + hour_angle / 360.0
    
    # Convert Julian dates to datetime objects
    def _julian_to_datetime(jd, tz):
        jd_frac = jd + 0.5
        z = int(jd_frac)
        f = jd_frac - z
        
        if z < 2299161:
            a = z
        else:
            alpha = int((z - 1867216.25) / 36524.25)
            a = z + 1 + alpha - int(alpha / 4)
            
        b = a + 1524
        c = int((b - 122.1) / 365.25)
        d = int(365.25 * c)
        e = int((b - d) / 30.6001)
        
        day = b - d - int(30.6001 * e) + f
        month = e - 1 if e < 14 else e - 13
        year = c - 4716 if month > 2 else c - 4715
        
        hour_frac = (day - int(day)) * 24
        hour = int(hour_frac)
        min_frac = (hour_frac - hour) * 60
        minute = int(min_frac)
        sec_frac = (min_frac - minute) * 60
        second = int(sec_frac)
        microsecond = int((sec_frac - second) * 1000000)
        
        dt = datetime.datetime(year, month, int(day), hour, minute, second, microsecond, tzinfo=tz)
        return dt
    
    rise_time = _julian_to_datetime(j_rise, tzinfo) if j_rise else None
    set_time = _julian_to_datetime(j_set, tzinfo) if j_set else None
    noon_time = _julian_to_datetime(j_transit, tzinfo)
    
    return rise_time, set_time, noon_time

def sun(observer, date=None, tzinfo=None):
    """Calculate all sun-related values for a date.
    
    Args:
        observer: LocationInfo observer attribute or similar
        date: The date for which to calculate the times. Default is today.
        tzinfo: The timezone to use for the returned times.
    
    Returns:
        A dictionary with keys 'dawn', 'sunrise', 'noon', 'sunset', 'dusk'
        containing the respective times as datetime objects.
    """
    if date is None:
        date = datetime.date.today()
    
    if tzinfo is None:
        tzinfo = datetime.timezone.utc
    
    # Sunrise/sunset zenith adjusted for elevation
    sunrise_sunset_zenith = 90 + _adjust_to_horizon(observer.elevation)
    
    # Civil dawn/dusk zenith angle (6 degrees below horizon)
    dawn_dusk_zenith = 96  # 90 + 6
    
    # Calculate times
    sunrise, sunset, noon = _calculate_sunrise_sunset(observer, date, tzinfo, sunrise_sunset_zenith)
    dawn, dusk, _ = _calculate_sunrise_sunset(observer, date, tzinfo, dawn_dusk_zenith)
    
    return {
        'dawn': dawn,
        'sunrise': sunrise,
        'noon': noon,
        'sunset': sunset,
        'dusk': dusk
    }

def sunrise(observer, date=None, tzinfo=None):
    """Calculate sunrise time for a specific observer and date."""
    return sun(observer, date, tzinfo)['sunrise']

def sunset(observer, date=None, tzinfo=None):
    """Calculate sunset time for a specific observer and date."""
    return sun(observer, date, tzinfo)['sunset']

def dawn(observer, date=None, tzinfo=None):
    """Calculate dawn time for a specific observer and date."""
    return sun(observer, date, tzinfo)['dawn']

def dusk(observer, date=None, tzinfo=None):
    """Calculate dusk time for a specific observer and date."""
    return sun(observer, date, tzinfo)['dusk']

def noon(observer, date=None, tzinfo=None):
    """Calculate solar noon time for a specific observer and date."""
    return sun(observer, date, tzinfo)['noon']