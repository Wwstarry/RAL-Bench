import datetime
import math

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

def phase(date=None):
    """Calculate the phase of the moon for a specific date.
    
    Args:
        date: The date for which to calculate the moon phase. Default is today.
    
    Returns:
        A float in the range 0-28 representing the age of the moon in days.
    """
    if date is None:
        date = datetime.date.today()
    
    # Convert to Julian date
    jd = _to_julian(date)
    
    # Reference date for the new moon (January 6, 2000)
    reference_new_moon = 2451550.1
    
    # Length of the lunar cycle in days
    lunar_cycle = 29.530588853
    
    # Calculate days since the reference new moon
    days_since_new = jd - reference_new_moon
    
    # Calculate the current position in the lunar cycle
    phase = days_since_new % lunar_cycle
    
    return phase