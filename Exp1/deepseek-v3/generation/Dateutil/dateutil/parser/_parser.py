"""
Date string parser implementation.
"""

import re
import datetime
from calendar import month_abbr, month_name
from dateutil import tz as tz_module

class parserinfo:
    """Parser information for date parsing."""
    
    # Months
    MONTHS = [(month_abbr[i].lower(), month_name[i].lower()) for i in range(1, 13)]
    
    # Weekdays
    WEEKDAYS = [
        ("mon", "monday"), ("tue", "tuesday"), ("wed", "wednesday"),
        ("thu", "thursday"), ("fri", "friday"), ("sat", "saturday"),
        ("sun", "sunday")
    ]
    
    # Timezone names (simplified)
    UTCZONE = "UTC"
    TIMEZONES = {
        "utc": tz_module.UTC,
        "gmt": tz_module.UTC,
        "z": tz_module.UTC,
    }

class parser:
    """Date string parser."""
    
    def __init__(self, info=None):
        self.info = info or parserinfo()
    
    def parse(self, timestr, default=None, ignoretz=False, tzinfos=None):
        return parse(timestr, default, ignoretz, tzinfos)

def parse(timestr, default=None, ignoretz=False, tzinfos=None):
    """
    Parse a datetime string into a datetime object.
    
    Args:
        timestr: String to parse
        default: Default datetime to use for missing parts
        ignoretz: Whether to ignore timezone information
        tzinfos: Additional timezone mappings
    
    Returns:
        datetime object
    """
    if default is None:
        default = datetime.datetime.now()
    
    # Basic regex patterns
    date_patterns = [
        # ISO format: YYYY-MM-DD
        r'(\d{4})-(\d{2})-(\d{2})',
        # DD/MM/YYYY or MM/DD/YYYY
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        # Month names
        r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})',
    ]
    
    time_patterns = [
        # HH:MM:SS
        r'(\d{1,2}):(\d{2}):(\d{2})',
        # HH:MM
        r'(\d{1,2}):(\d{2})',
    ]
    
    tz_patterns = [
        # Timezone offsets: +HH:MM, -HHMM, Z
        r'([+-])(\d{2}):?(\d{2})',
        r'(Z)',
        # Timezone names
        r'([A-Z]{3,})',
    ]
    
    # Combine patterns
    full_pattern = (
        r'^(.+?)(?:\s+(' + '|'.join([p.strip('()') for p in time_patterns]) + 
        r'))?(?:\s*(' + '|'.join([p.strip('()') for p in tz_patterns]) + r'))?$'
    )
    
    match = re.match(full_pattern, timestr.strip())
    if not match:
        raise ValueError(f"Unable to parse date string: {timestr}")
    
    date_part = match.group(1)
    time_part = match.group(2) if match.group(2) else "00:00:00"
    tz_part = match.group(3) if match.group(3) else ""
    
    # Parse date part
    year, month, day = _parse_date_part(date_part, default)
    
    # Parse time part  
    hour, minute, second = _parse_time_part(time_part)
    
    # Create datetime
    dt = datetime.datetime(year, month, day, hour, minute, second)
    
    # Handle timezone
    if not ignoretz and tz_part:
        tzinfo = _parse_timezone(tz_part, tzinfos)
        if tzinfo:
            dt = dt.replace(tzinfo=tzinfo)
    
    return dt

def _parse_date_part(date_str, default):
    """Parse the date portion of the string."""
    # Try different date formats
    patterns = [
        # YYYY-MM-DD
        (r'(\d{4})-(\d{2})-(\d{2})', lambda y, m, d: (int(y), int(m), int(d))),
        # DD/MM/YYYY or MM/DD/YYYY (assume DD/MM/YYYY)
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', lambda d, m, y: (int(y), int(m), int(d))),
        # Month names
        (r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', _parse_month_name_date),
    ]
    
    for pattern, converter in patterns:
        match = re.match(pattern, date_str.strip())
        if match:
            return converter(*match.groups())
    
    # If no pattern matches, use default
    return default.year, default.month, default.day

def _parse_month_name_date(month_str, day_str, year_str):
    """Parse date with month name."""
    month_names = {name.lower(): i for i, (abbr, full) in enumerate(parserinfo.MONTHS, 1) 
                  for name in [abbr, full]}
    
    month_lower = month_str.lower()
    if month_lower in month_names:
        month = month_names[month_lower]
    else:
        month = 1  # Default to January
    
    return int(year_str), month, int(day_str)

def _parse_time_part(time_str):
    """Parse the time portion of the string."""
    patterns = [
        # HH:MM:SS
        (r'(\d{1,2}):(\d{2}):(\d{2})', lambda h, m, s: (int(h), int(m), int(s))),
        # HH:MM
        (r'(\d{1,2}):(\d{2})', lambda h, m: (int(h), int(m), 0)),
    ]
    
    for pattern, converter in patterns:
        match = re.match(pattern, time_str.strip())
        if match:
            return converter(*match.groups())
    
    return 0, 0, 0  # Default to midnight

def _parse_timezone(tz_str, tzinfos):
    """Parse timezone information."""
    if not tzinfos:
        tzinfos = {}
    
    # Check if it's a known timezone name
    tz_lower = tz_str.upper()
    if tz_lower in parserinfo.TIMEZONES:
        return parserinfo.TIMEZONES[tz_lower]
    
    # Check user-provided timezone mappings
    if tz_str in tzinfos:
        return tzinfos[tz_str]
    
    # Try to parse offset
    offset_patterns = [
        # ±HH:MM or ±HHMM
        (r'([+-])(\d{2}):?(\d{2})', _parse_offset_timezone),
        # Z (UTC)
        (r'Z', lambda: tz_module.UTC),
    ]
    
    for pattern, converter in offset_patterns:
        match = re.match(pattern, tz_str)
        if match:
            return converter(*match.groups()) if match.groups() else converter()
    
    return None

def _parse_offset_timezone(sign, hours, minutes):
    """Parse timezone offset."""
    total_minutes = int(hours) * 60 + int(minutes)
    if sign == '-':
        total_minutes = -total_minutes
    
    return tz_module.tzoffset(None, total_minutes * 60)