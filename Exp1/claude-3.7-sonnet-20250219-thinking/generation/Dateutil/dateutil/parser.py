from datetime import datetime, timedelta, tzinfo
import re
from . import tz

class parserinfo:
    """Class used to specify various parsing options."""
    def __init__(self, dayfirst=False, yearfirst=False):
        self.dayfirst = dayfirst
        self.yearfirst = yearfirst
        
        self.JUMP = [' ', '.', ',', ';', '-', '/', "'", 'at', 'on', 'and', 'ad', 'm', 't', 'of', 'st', 'nd', 'rd', 'th']
        
        self.WEEKDAYS = [
            ('Mon', 'Monday'),
            ('Tue', 'Tuesday'), 
            ('Wed', 'Wednesday'),
            ('Thu', 'Thursday'),
            ('Fri', 'Friday'),
            ('Sat', 'Saturday'),
            ('Sun', 'Sunday')
        ]
        
        self.MONTHS = [
            ('Jan', 'January'),
            ('Feb', 'February'),
            ('Mar', 'March'),
            ('Apr', 'April'),
            ('May', 'May'),
            ('Jun', 'June'),
            ('Jul', 'July'),
            ('Aug', 'August'),
            ('Sep', 'September'),
            ('Oct', 'October'),
            ('Nov', 'November'),
            ('Dec', 'December')
        ]

def parse(timestr, parserinfo=None, **kwargs):
    """
    Parse a string representing a date/time and return a datetime object.
    
    :param timestr: The string to parse
    :param parserinfo: Optional ParserInfo object
    :param kwargs: Additional keyword arguments:
                  - default: Default datetime object if parsing fails
                  - ignoretz: If True, timezone in the string will be ignored
                  - tzinfos: Additional timezone info
                  - fuzzy: If True, unknown tokens will be ignored
    :return: A datetime object
    """
    default = kwargs.get('default', None)
    ignoretz = kwargs.get('ignoretz', False)
    tzinfos = kwargs.get('tzinfos', {})
    fuzzy = kwargs.get('fuzzy', False)
    
    # Handle ISO format
    iso_match = re.match(
        r'(\d{4})-?(\d{1,2})-?(\d{1,2})[T ]?(\d{1,2}):?(\d{1,2}):?(\d{1,2})(?:\.(\d+))?(?:([+-])(\d{2}):?(\d{2})|Z)?',
        timestr
    )
    
    if iso_match:
        year, month, day, hour, minute, second = map(int, iso_match.groups()[:6])
        
        microsecond = 0
        if iso_match.group(7):
            microsecond = int(iso_match.group(7).ljust(6, '0')[:6])
        
        tzinfo_obj = None
        if not ignoretz:
            if iso_match.group(8) == '+' or iso_match.group(8) == '-':
                sign = 1 if iso_match.group(8) == '+' else -1
                hours_offset = int(iso_match.group(9))
                minutes_offset = int(iso_match.group(10))
                tzname = f"{iso_match.group(8)}{hours_offset:02d}:{minutes_offset:02d}"
                tzinfo_obj = tz.tzoffset(tzname, sign * (hours_offset * 3600 + minutes_offset * 60))
            elif 'Z' in timestr:
                tzinfo_obj = tz.UTC
            elif tzinfos:
                for tz_name, tz_obj in tzinfos.items():
                    if tz_name in timestr:
                        tzinfo_obj = tz_obj
                        break
        
        return datetime(year, month, day, hour, minute, second, microsecond, tzinfo_obj)
    
    # Handle common formats
    # MM/DD/YYYY or DD/MM/YYYY
    date_formats = [
        r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})', # MM/DD/YYYY or DD/MM/YYYY
        r'(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})',   # YYYY-MM-DD
        r'(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})' # Month Day, Year
    ]
    
    for pattern in date_formats:
        date_match = re.search(pattern, timestr)
        if date_match:
            groups = date_match.groups()
            
            # Try to determine format based on parserinfo or pattern
            if pattern == date_formats[0]:
                # MM/DD/YYYY or DD/MM/YYYY
                if parserinfo and parserinfo.dayfirst:
                    day, month, year = map(int, groups)
                else:
                    month, day, year = map(int, groups)
            elif pattern == date_formats[1]:
                # YYYY-MM-DD
                year, month, day = map(int, groups)
            else:
                # Month name format
                month_name = groups[0].lower()
                day = int(groups[1])
                year = int(groups[2])
                
                month = 1  # Default
                for i, (abbr, full) in enumerate(parserinfo.MONTHS if parserinfo else []):
                    if month_name.startswith(abbr.lower()) or month_name.startswith(full.lower()):
                        month = i + 1
                        break
            
            # Handle 2-digit years
            if year < 100:
                if year < 50:
                    year += 2000
                else:
                    year += 1900
            
            # Look for time part
            time_match = re.search(r'(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\s*(am|pm))?', timestr, re.IGNORECASE)
            hour, minute, second = 0, 0, 0
            
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                second = int(time_match.group(3)) if time_match.group(3) else 0
                
                # Handle AM/PM
                if time_match.group(4) and time_match.group(4).lower() == 'pm' and hour < 12:
                    hour += 12
                elif time_match.group(4) and time_match.group(4).lower() == 'am' and hour == 12:
                    hour = 0
            
            # Handle timezone
            tzinfo_obj = None
            if not ignoretz:
                tz_match = re.search(r'(?:GMT|UTC)?([+-])(\d{1,2})(?::?(\d{2}))?', timestr)
                if tz_match:
                    sign = 1 if tz_match.group(1) == '+' else -1
                    tz_hour = int(tz_match.group(2))
                    tz_minute = int(tz_match.group(3)) if tz_match.group(3) else 0
                    tzname = f"{tz_match.group(1)}{tz_hour:02d}:{tz_minute:02d}"
                    tzinfo_obj = tz.tzoffset(tzname, sign * (tz_hour * 3600 + tz_minute * 60))
                elif tzinfos:
                    for tz_name, tz_obj in tzinfos.items():
                        if tz_name in timestr:
                            tzinfo_obj = tz_obj
                            break
            
            try:
                return datetime(year, month, day, hour, minute, second, 0, tzinfo_obj)
            except ValueError:
                # Handle invalid dates (e.g., Feb 30)
                pass
    
    # Return default if we can't parse
    if default:
        return default
    
    raise ValueError(f"Failed to parse: {timestr}")