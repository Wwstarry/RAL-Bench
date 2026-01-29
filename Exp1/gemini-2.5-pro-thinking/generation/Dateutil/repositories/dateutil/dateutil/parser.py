import datetime
import re
from . import tz

class ParserError(ValueError):
    """
    Exception raised for parsing errors.
    """
    pass

# A map for month names to their numeric representation
_MONTHS = {
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

def _parse_tz_string(tz_str, ignoretz=False):
    """
    Parses a timezone string and returns a tzinfo object.
    """
    if ignoretz or not tz_str:
        return None
    
    tz_str = tz_str.strip()
    if tz_str.upper() == 'Z':
        return tz.UTC

    # Check for known abbreviations first
    tzinfo = tz.gettz(tz_str)
    if tzinfo:
        return tzinfo

    # Check for numeric offsets like +0000, -0800, +05:30
    m = re.match(r'([+-])(\d{2}):?(\d{2})?$', tz_str)
    if m:
        sign, h, m_str = m.groups()
        m_val = int(m_str) if m_str else 0
        offset_seconds = (int(h) * 3600 + m_val * 60)
        if sign == '-':
            offset_seconds = -offset_seconds
        return tz.tzoffset(tz_str, offset_seconds)
        
    return None

def parse(timestr, default=None, ignoretz=False, **kwargs):
    """
    Parse a string containing a date/time into a datetime object.
    """
    if not isinstance(timestr, str):
        raise TypeError("str object expected")

    # Handle ISO 8601 format, which is common and unambiguous.
    # datetime.fromisoformat doesn't handle 'Z' until Python 3.11.
    try:
        ts_to_parse = timestr
        if timestr.endswith('Z'):
            ts_to_parse = timestr[:-1] + '+00:00'
        
        dt = datetime.datetime.fromisoformat(ts_to_parse)
        if ignoretz:
            dt = dt.replace(tzinfo=None)
        return dt
    except (ValueError, TypeError):
        # Fallback to more general parsing
        pass

    # General-purpose parsing logic
    s = timestr.strip()
    
    # Default values
    now = default or datetime.datetime.now()
    year, month, day = now.year, now.month, now.day
    hour, minute, second, microsecond = 0, 0, 0, 0
    tzinfo = None
    
    # A simplified regex to capture common date/time/tz patterns
    # This is not exhaustive but covers many cases.
    # Pattern for time with optional seconds, microseconds, and AM/PM
    time_regex = r'(\d{1,2}):(\d{1,2})(?::(\d{1,2})(?:\.(\d+))?)?\s*(am|pm)?'
    # Pattern for timezone info
    tz_regex = r'\s*([a-z]{3,5}|[+-]\d{2}:?\d{2}|z)\b'

    time_match = re.search(time_regex, s, re.IGNORECASE)
    if time_match:
        h, m, sec, us, ampm = time_match.groups()
        hour, minute = int(h), int(m)
        second = int(sec) if sec else 0
        microsecond = int(us.ljust(6, '0')[:6]) if us else 0
        
        if ampm and ampm.lower() == 'pm' and hour < 12:
            hour += 12
        if ampm and ampm.lower() == 'am' and hour == 12:
            hour = 0
            
        # Remove the matched time part to simplify date parsing
        s = s[:time_match.start()] + s[time_match.end():]

    tz_match = re.search(tz_regex, s, re.IGNORECASE)
    if tz_match:
        tzinfo = _parse_tz_string(tz_match.group(1), ignoretz)
        s = s[:tz_match.start()] + s[tz_match.end():]

    # Clean up and split the remaining string for date parts
    s = re.sub(r'[,\-/.]+', ' ', s).strip()
    parts = [p for p in s.split() if p]

    found_date = False
    if len(parts) >= 3:
        # Try to find Y, M, D from three parts
        p1, p2, p3 = parts[0], parts[1], parts[2]
        
        # Case 1: Month name is present
        if p1.lower()[:3] in _MONTHS: # "Mon Day Year"
            month = _MONTHS[p1.lower()[:3]]
            day = int(p2)
            year = int(p3)
            found_date = True
        elif p2.lower()[:3] in _MONTHS: # "Day Mon Year" or "Year Mon Day"
            month = _MONTHS[p2.lower()[:3]]
            if len(p1) == 4 and p1.isdigit(): # "Year Mon Day"
                year = int(p1)
                day = int(p3)
            else: # "Day Mon Year"
                day = int(p1)
                year = int(p3)
            found_date = True
        
        # Case 2: All numeric
        if not found_date:
            try:
                # Assume YYYY-MM-DD or similar
                vals = [int(p) for p in parts[:3]]
                if vals[0] > 31: # Likely Y M D
                    year, month, day = vals[0], vals[1], vals[2]
                elif vals[2] > 31: # Likely D M Y or M D Y
                    year = vals[2]
                    # Ambiguous M/D, assume M D Y for simplicity
                    month, day = vals[0], vals[1]
                else: # Ambiguous, default to Y M D
                    year, month, day = vals[0], vals[1], vals[2]
                found_date = True
            except (ValueError, IndexError):
                pass

    if not found_date and len(parts) == 1 and len(parts[0]) >= 8 and parts[0].isdigit():
        # YYYYMMDD format
        p = parts[0]
        year, month, day = int(p[0:4]), int(p[4:6]), int(p[6:8])
        found_date = True

    if year < 100:
        year += 2000 if year < 69 else 1900

    try:
        return datetime.datetime(year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)
    except ValueError as e:
        raise ParserError(str(e))