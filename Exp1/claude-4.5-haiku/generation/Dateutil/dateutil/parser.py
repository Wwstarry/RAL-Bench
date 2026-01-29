"""
Parsing of date and time strings
"""

import re
from datetime import datetime, date, time, timedelta
from typing import Optional, Tuple, Union
from dateutil import tz as tz_module


class ParserError(ValueError):
    """Error raised when parsing fails"""
    pass


def parse(timestr: str, dayfirst: bool = False, yearfirst: bool = False,
          fuzzy: bool = False, fuzzy_with_tokens: bool = False,
          default: Optional[datetime] = None) -> Union[datetime, Tuple[datetime, list]]:
    """
    Parse a string in one of the supported formats to a datetime object.
    
    Args:
        timestr: String to parse
        dayfirst: Whether to interpret the first value in an ambiguous 3-integer date as the day
        yearfirst: Whether to interpret the first value in an ambiguous 3-integer date as the year
        fuzzy: Allow fuzzy parsing
        fuzzy_with_tokens: Return tokens along with parsed datetime
        default: Default datetime to use for missing components
        
    Returns:
        datetime object, or tuple of (datetime, tokens) if fuzzy_with_tokens=True
    """
    if default is None:
        default = datetime(1900, 1, 1)
    
    parser = _DatetimeParser(dayfirst=dayfirst, yearfirst=yearfirst, fuzzy=fuzzy)
    res, tokens = parser.parse(timestr, default=default)
    
    if fuzzy_with_tokens:
        return res, tokens
    return res


class _DatetimeParser:
    """Internal parser for datetime strings"""
    
    MONTHS = {
        'jan': 1, 'january': 1,
        'feb': 2, 'february': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'september': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12,
    }
    
    WEEKDAYS = {
        'mon': 0, 'monday': 0,
        'tue': 1, 'tuesday': 1,
        'wed': 2, 'wednesday': 2,
        'thu': 3, 'thursday': 3,
        'fri': 4, 'friday': 4,
        'sat': 5, 'saturday': 5,
        'sun': 6, 'sunday': 6,
    }
    
    def __init__(self, dayfirst=False, yearfirst=False, fuzzy=False):
        self.dayfirst = dayfirst
        self.yearfirst = yearfirst
        self.fuzzy = fuzzy
    
    def parse(self, timestr: str, default: datetime) -> Tuple[datetime, list]:
        """Parse a datetime string"""
        tokens = []
        
        # Try ISO 8601 format first
        result = self._parse_iso8601(timestr)
        if result:
            return result, tokens
        
        # Try common formats
        result = self._parse_common_formats(timestr, default)
        if result:
            return result, tokens
        
        # Fallback to fuzzy parsing
        if self.fuzzy:
            result = self._parse_fuzzy(timestr, default)
            if result:
                return result, tokens
        
        raise ParserError(f"Unknown string format: {timestr}")
    
    def _parse_iso8601(self, timestr: str) -> Optional[Tuple[datetime, list]]:
        """Parse ISO 8601 format strings"""
        timestr = timestr.strip()
        
        # Pattern for ISO 8601: YYYY-MM-DD[T ]HH:MM:SS[.fff][+HH:MM or Z]
        iso_pattern = r'^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?)?(?:Z|([+-]\d{2}):(\d{2}))?$'
        match = re.match(iso_pattern, timestr)
        
        if match:
            year, month, day, hour, minute, second, microsecond, tz_hour, tz_minute = match.groups()
            
            year = int(year)
            month = int(month)
            day = int(day)
            hour = int(hour) if hour else 0
            minute = int(minute) if minute else 0
            second = int(second) if second else 0
            
            if microsecond:
                # Pad or truncate to 6 digits
                microsecond = int(microsecond.ljust(6, '0')[:6])
            else:
                microsecond = 0
            
            tzinfo = None
            if timestr.endswith('Z'):
                tzinfo = tz_module.UTC
            elif tz_hour is not None:
                offset_hours = int(tz_hour)
                offset_minutes = int(tz_minute) if tz_minute else 0
                if offset_hours < 0:
                    offset_minutes = -offset_minutes
                offset = timedelta(hours=offset_hours, minutes=offset_minutes)
                tzinfo = tz_module.tzoffset(None, offset)
            
            dt = datetime(year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)
            return dt, []
        
        return None
    
    def _parse_common_formats(self, timestr: str, default: datetime) -> Optional[Tuple[datetime, list]]:
        """Parse common date/time formats"""
        timestr = timestr.strip()
        
        # Try various common patterns
        patterns = [
            # YYYY-MM-DD HH:MM:SS
            (r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})$',
             lambda m: self._make_datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                                          int(m.group(4)), int(m.group(5)), int(m.group(6)), 0, None)),
            # YYYY-MM-DD HH:MM
            (r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})$',
             lambda m: self._make_datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                                          int(m.group(4)), int(m.group(5)), 0, 0, None)),
            # YYYY-MM-DD
            (r'^(\d{4})-(\d{2})-(\d{2})$',
             lambda m: self._make_datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                                          0, 0, 0, 0, None)),
            # MM/DD/YYYY HH:MM:SS
            (r'^(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{2}):(\d{2}):(\d{2})$',
             lambda m: self._parse_mdy_hms(m, default)),
            # MM/DD/YYYY
            (r'^(\d{1,2})/(\d{1,2})/(\d{4})$',
             lambda m: self._parse_mdy(m, default)),
            # DD/MM/YYYY HH:MM:SS
            (r'^(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{2}):(\d{2}):(\d{2})$',
             lambda m: self._parse_dmy_hms(m, default) if self.dayfirst else self._parse_mdy_hms(m, default)),
            # DD/MM/YYYY
            (r'^(\d{1,2})/(\d{1,2})/(\d{4})$',
             lambda m: self._parse_dmy(m, default) if self.dayfirst else self._parse_mdy(m, default)),
        ]
        
        for pattern, handler in patterns:
            match = re.match(pattern, timestr)
            if match:
                try:
                    return handler(match), []
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _parse_fuzzy(self, timestr: str, default: datetime) -> Optional[datetime]:
        """Parse with fuzzy matching"""
        # Extract numbers and known date/time components
        parts = timestr.split()
        
        year = None
        month = None
        day = None
        hour = None
        minute = None
        second = None
        
        for part in parts:
            part_lower = part.lower().rstrip('.,')
            
            # Check for month names
            if part_lower in self.MONTHS:
                month = self.MONTHS[part_lower]
                continue
            
            # Check for numbers
            if re.match(r'^\d+$', part):
                num = int(part)
                if num > 31:
                    if year is None:
                        year = num
                elif day is None:
                    day = num
                elif month is None:
                    month = num
        
        if year and month and day:
            return self._make_datetime(year, month, day, 0, 0, 0, 0, None)
        
        return None
    
    def _make_datetime(self, year, month, day, hour, minute, second, microsecond, tzinfo):
        """Create a datetime object"""
        return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)
    
    def _parse_mdy(self, match, default):
        """Parse MM/DD/YYYY format"""
        month = int(match.group(1))
        day = int(match.group(2))
        year = int(match.group(3))
        return self._make_datetime(year, month, day, 0, 0, 0, 0, None)
    
    def _parse_mdy_hms(self, match, default):
        """Parse MM/DD/YYYY HH:MM:SS format"""
        month = int(match.group(1))
        day = int(match.group(2))
        year = int(match.group(3))
        hour = int(match.group(4))
        minute = int(match.group(5))
        second = int(match.group(6))
        return self._make_datetime(year, month, day, hour, minute, second, 0, None)
    
    def _parse_dmy(self, match, default):
        """Parse DD/MM/YYYY format"""
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))
        return self._make_datetime(year, month, day, 0, 0, 0, 0, None)
    
    def _parse_dmy_hms(self, match, default):
        """Parse DD/MM/YYYY HH:MM:SS format"""
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))
        hour = int(match.group(4))
        minute = int(match.group(5))
        second = int(match.group(6))
        return self._make_datetime(year, month, day, hour, minute, second, 0, None)