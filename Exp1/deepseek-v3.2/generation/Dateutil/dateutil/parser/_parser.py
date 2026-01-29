"""
Date and time string parser implementation.
"""

import re
import datetime
import calendar
from typing import Optional, Union, Dict, Any, List, Tuple
from .. import tz as tz_module

# Constants
DEFAULT_YEAR = datetime.datetime.now().year
DEFAULT_MONTH = 1
DEFAULT_DAY = 1
DEFAULT_HOUR = 0
DEFAULT_MINUTE = 0
DEFAULT_SECOND = 0
DEFAULT_MICROSECOND = 0

# Month name mappings
MONTHNAMES = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

# Weekday name mappings
WEEKDAYS = {
    "mon": 0, "monday": 0,
    "tue": 1, "tuesday": 1,
    "wed": 2, "wednesday": 2,
    "thu": 3, "thursday": 3,
    "fri": 4, "friday": 4,
    "sat": 5, "saturday": 5,
    "sun": 6, "sunday": 6,
}

# Timezone abbreviations (partial list)
TZINFOS = {
    "UTC": tz_module.UTC,
    "GMT": tz_module.UTC,
    "Z": tz_module.UTC,
}

# Regex patterns
DATE_PATTERNS = [
    # ISO 8601: 2023-12-25
    r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})',
    # US format: 12/25/2023
    r'(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{4})',
    # European format: 25.12.2023
    r'(?P<day>\d{1,2})\.(?P<month>\d{1,2})\.(?P<year>\d{4})',
]

TIME_PATTERNS = [
    # 14:30:45
    r'(?P<hour>\d{1,2}):(?P<minute>\d{1,2})(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6}))?)?',
    # 14:30
    r'(?P<hour>\d{1,2}):(?P<minute>\d{1,2})',
]

TZ_PATTERNS = [
    # +05:30, -08:00
    r'(?P<tzsign>[+-])(?P<tzhour>\d{2}):?(?P<tzminute>\d{2})',
    # Z
    r'Z',
]

class ParserError(ValueError):
    """Exception raised when parsing fails."""
    pass

def parse(timestr: str, 
          default: Optional[datetime.datetime] = None,
          ignoretz: bool = False,
          tzinfos: Optional[Dict[str, Any]] = None,
          **kwargs) -> datetime.datetime:
    """
    Parse a datetime string into a datetime object.
    
    Args:
        timestr: String to parse
        default: Default datetime to use for missing components
        ignoretz: If True, timezone info is ignored
        tzinfos: Additional timezone info mappings
        **kwargs: Additional arguments (for compatibility)
        
    Returns:
        datetime.datetime object
        
    Raises:
        ParserError: If parsing fails
    """
    if default is None:
        default = datetime.datetime(
            DEFAULT_YEAR, DEFAULT_MONTH, DEFAULT_DAY,
            DEFAULT_HOUR, DEFAULT_MINUTE, DEFAULT_SECOND, DEFAULT_MICROSECOND
        )
    
    # Merge provided tzinfos with defaults
    all_tzinfos = TZINFOS.copy()
    if tzinfos:
        all_tzinfos.update(tzinfos)
    
    # Parse components
    components = {
        'year': default.year,
        'month': default.month,
        'day': default.day,
        'hour': default.hour,
        'minute': default.minute,
        'second': default.second,
        'microsecond': default.microsecond,
        'tzinfo': default.tzinfo,
    }
    
    # Convert to lowercase for case-insensitive matching
    timestr_lower = timestr.lower()
    
    # Try to parse month names
    for month_name, month_num in MONTHNAMES.items():
        if month_name in timestr_lower:
            components['month'] = month_num
            # Remove month name to simplify further parsing
            timestr = re.sub(month_name, '', timestr_lower, flags=re.IGNORECASE)
            break
    
    # Try to parse weekday names (for informational purposes, not used in date calculation)
    for weekday_name in WEEKDAYS:
        if weekday_name in timestr_lower:
            # Remove weekday name
            timestr = re.sub(weekday_name, '', timestr_lower, flags=re.IGNORECASE)
            break
    
    # Parse date
    date_found = False
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, timestr)
        if match:
            date_found = True
            groups = match.groupdict()
            if 'year' in groups:
                components['year'] = int(groups['year'])
            if 'month' in groups:
                components['month'] = int(groups['month'])
            if 'day' in groups:
                components['day'] = int(groups['day'])
            # Remove date part to simplify time parsing
            timestr = timestr[:match.start()] + timestr[match.end():]
            break
    
    # Parse time
    time_found = False
    for pattern in TIME_PATTERNS:
        match = re.search(pattern, timestr)
        if match:
            time_found = True
            groups = match.groupdict()
            if 'hour' in groups:
                components['hour'] = int(groups['hour'])
            if 'minute' in groups:
                components['minute'] = int(groups['minute'])
            if 'second' in groups and groups['second']:
                components['second'] = int(groups['second'])
            if 'microsecond' in groups and groups['microsecond']:
                microsecond = groups['microsecond']
                # Pad to 6 digits
                microsecond = microsecond.ljust(6, '0')[:6]
                components['microsecond'] = int(microsecond)
            # Remove time part
            timestr = timestr[:match.start()] + timestr[match.end():]
            break
    
    # Parse timezone
    tzinfo = None
    if not ignoretz:
        for pattern in TZ_PATTERNS:
            match = re.search(pattern, timestr, re.IGNORECASE)
            if match:
                groups = match.groupdict()
                if 'tzsign' in groups:
                    # Offset timezone
                    sign = 1 if groups['tzsign'] == '+' else -1
                    tzhour = int(groups['tzhour'])
                    tzminute = int(groups['tzminute'])
                    offset = sign * (tzhour * 3600 + tzminute * 60)
                    tzinfo = tz_module.tzoffset(None, offset)
                elif match.group() == 'Z':
                    tzinfo = tz_module.UTC
                break
        
        # Check for timezone abbreviations
        if not tzinfo:
            # Look for timezone abbreviations in the remaining string
            remaining = timestr.strip()
            if remaining in all_tzinfos:
                tzinfo = all_tzinfos[remaining]
    
    components['tzinfo'] = tzinfo
    
    # Validate components
    try:
        dt = datetime.datetime(
            year=components['year'],
            month=components['month'],
            day=components['day'],
            hour=components['hour'],
            minute=components['minute'],
            second=components['second'],
            microsecond=components['microsecond'],
            tzinfo=components['tzinfo']
        )
    except ValueError as e:
        raise ParserError(f"Failed to parse datetime from '{timestr}': {e}")
    
    return dt