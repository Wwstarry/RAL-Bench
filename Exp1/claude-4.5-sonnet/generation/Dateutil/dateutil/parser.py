"""
Date and datetime parsing utilities.
"""

import re
from datetime import datetime, timedelta
from dateutil import tz as tzmodule


class ParserError(ValueError):
    """Exception raised for parsing errors."""
    pass


def parse(timestr, default=None, ignoretz=False, tzinfos=None, **kwargs):
    """
    Parse a string in one of the supported formats to a datetime object.
    
    Args:
        timestr: String to parse
        default: Default datetime to use for missing components
        ignoretz: If True, ignore timezone information
        tzinfos: Additional timezone information
        
    Returns:
        datetime object
    """
    if default is None:
        default = datetime(1, 1, 1, 0, 0, 0)
    
    if not timestr or not isinstance(timestr, str):
        raise ParserError("Invalid date string")
    
    timestr = timestr.strip()
    
    # Try ISO 8601 format with timezone
    # Format: YYYY-MM-DDTHH:MM:SS+HH:MM or YYYY-MM-DDTHH:MM:SSZ
    iso_tz_pattern = r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:\d{2})$'
    match = re.match(iso_tz_pattern, timestr)
    if match:
        year, month, day, hour, minute, second, microsecond, tzstr = match.groups()
        year, month, day = int(year), int(month), int(day)
        hour, minute, second = int(hour), int(minute), int(second)
        
        if microsecond:
            # Pad or truncate to 6 digits
            microsecond = microsecond.ljust(6, '0')[:6]
            microsecond = int(microsecond)
        else:
            microsecond = 0
        
        if ignoretz:
            tzinfo = None
        elif tzstr == 'Z':
            tzinfo = tzmodule.UTC
        else:
            # Parse offset like +05:30 or -08:00
            sign = 1 if tzstr[0] == '+' else -1
            tz_hours = int(tzstr[1:3])
            tz_minutes = int(tzstr[4:6])
            offset = timedelta(hours=sign * tz_hours, minutes=sign * tz_minutes)
            tzinfo = tzmodule.tzoffset(None, offset)
        
        return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)
    
    # Try ISO 8601 format without timezone
    iso_pattern = r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?$'
    match = re.match(iso_pattern, timestr)
    if match:
        year, month, day, hour, minute, second, microsecond = match.groups()
        year, month, day = int(year), int(month), int(day)
        hour, minute, second = int(hour), int(minute), int(second)
        
        if microsecond:
            microsecond = microsecond.ljust(6, '0')[:6]
            microsecond = int(microsecond)
        else:
            microsecond = 0
        
        return datetime(year, month, day, hour, minute, second, microsecond)
    
    # Try simple date format YYYY-MM-DD
    date_pattern = r'^(\d{4})-(\d{2})-(\d{2})$'
    match = re.match(date_pattern, timestr)
    if match:
        year, month, day = match.groups()
        year, month, day = int(year), int(month), int(day)
        return datetime(year, month, day, default.hour, default.minute, default.second, default.microsecond)
    
    # Try format with timezone name: YYYY-MM-DD HH:MM:SS TIMEZONE
    tz_name_pattern = r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})\s+([A-Z]{3,4})$'
    match = re.match(tz_name_pattern, timestr)
    if match:
        year, month, day, hour, minute, second, tzname = match.groups()
        year, month, day = int(year), int(month), int(day)
        hour, minute, second = int(hour), int(minute), int(second)
        
        if ignoretz:
            tzinfo = None
        else:
            tzinfo = tzmodule.gettz(tzname)
            if tzinfo is None:
                tzinfo = None
        
        return datetime(year, month, day, hour, minute, second, tzinfo=tzinfo)
    
    # Try datetime without timezone: YYYY-MM-DD HH:MM:SS
    datetime_pattern = r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})$'
    match = re.match(datetime_pattern, timestr)
    if match:
        year, month, day, hour, minute, second = match.groups()
        year, month, day = int(year), int(month), int(day)
        hour, minute, second = int(hour), int(minute), int(second)
        return datetime(year, month, day, hour, minute, second)
    
    # Try human-friendly formats like "January 1, 2020"
    month_names = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    # Try "Month Day, Year" format
    month_day_year_pattern = r'^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$'
    match = re.match(month_day_year_pattern, timestr)
    if match:
        month_str, day, year = match.groups()
        month = month_names.get(month_str.lower())
        if month:
            return datetime(int(year), month, int(day))
    
    # Try "Day Month Year" format
    day_month_year_pattern = r'^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$'
    match = re.match(day_month_year_pattern, timestr)
    if match:
        day, month_str, year = match.groups()
        month = month_names.get(month_str.lower())
        if month:
            return datetime(int(year), month, int(day))
    
    raise ParserError(f"Unable to parse date string: {timestr}")