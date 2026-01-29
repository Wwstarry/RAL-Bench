import re
from datetime import datetime as _datetime

def parse_iso8601(date_string):
    """Parse an ISO 8601 date string."""
    date_string = date_string.strip()
    
    iso_pattern = r'^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?)?(?:Z|([+-]\d{2}):(\d{2}))?$'
    match = re.match(iso_pattern, date_string)
    
    if not match:
        return None
    
    year, month, day, hour, minute, second, microsecond_str, tz_hour, tz_minute = match.groups()
    
    year = int(year)
    month = int(month)
    day = int(day)
    hour = int(hour) if hour else 0
    minute = int(minute) if minute else 0
    second = int(second) if second else 0
    
    if microsecond_str:
        microsecond = int(microsecond_str.ljust(6, '0')[:6])
    else:
        microsecond = 0
    
    tz = None
    if date_string.endswith('Z'):
        tz = 'UTC'
    elif tz_hour is not None:
        tz_offset_hours = int(tz_hour)
        tz_offset_minutes = int(tz_minute) if tz_minute else 0
        tz = f"UTC{tz_offset_hours:+03d}:{tz_offset_minutes:02d}"
    
    return {
        'year': year,
        'month': month,
        'day': day,
        'hour': hour,
        'minute': minute,
        'second': second,
        'microsecond': microsecond,
        'tz': tz
    }