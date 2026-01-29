"""
A simplified pure Python dateutil.parser module implementing parse()
for a wide range of date/time string formats, including ISO-8601 and
common human-friendly formats, returning datetime objects with tzinfo.
"""

import re
import datetime
from dateutil import tz

__all__ = ['parse']

# Regex patterns for ISO8601 and common date/time formats
_iso8601_re = re.compile(
    r'^\s*(?P<year>\d{4})'
    r'(?:-(?P<month>\d{2})'
    r'(?:-(?P<day>\d{2})'
    r'(?:[T\s](?P<hour>\d{2}):(?P<minute>\d{2})'
    r'(?::(?P<second>\d{2})(?:\.(?P<microsecond>\d+))?)?'
    r'(?P<tz>Z|[+\-]\d{2}:?\d{2})?)?)?)?\s*$'
)

# Common month name mapping
_months = {
    'jan':1, 'feb':2, 'mar':3, 'apr':4, 'may':5, 'jun':6,
    'jul':7, 'aug':8, 'sep':9, 'oct':10, 'nov':11, 'dec':12
}

# Weekday names for parsing (not used here but could be extended)
_weekdays = {
    'mon':0, 'tue':1, 'wed':2, 'thu':3, 'fri':4, 'sat':5, 'sun':6
}

def _parse_iso8601(text):
    m = _iso8601_re.match(text)
    if not m:
        return None
    gd = m.groupdict()
    year = int(gd['year'])
    month = int(gd['month'] or 1)
    day = int(gd['day'] or 1)
    hour = int(gd['hour'] or 0)
    minute = int(gd['minute'] or 0)
    second = int(gd['second'] or 0)
    microsecond = 0
    if gd['microsecond']:
        # Pad or truncate to microseconds (6 digits)
        ms = gd['microsecond'][:6].ljust(6, '0')
        microsecond = int(ms)
    tzinfo = None
    if gd['tz']:
        tzstr = gd['tz']
        if tzstr == 'Z':
            tzinfo = tz.UTC
        else:
            # Parse offset like +HH:MM or +HHMM
            sign = 1 if tzstr[0] == '+' else -1
            tzstr = tzstr[1:]
            if ':' in tzstr:
                hh, mm = tzstr.split(':')
            else:
                hh, mm = tzstr[:2], tzstr[2:]
            offset = sign * (int(hh)*3600 + int(mm)*60)
            tzinfo = tz.tzoffset(None, offset)
    try:
        dt = datetime.datetime(year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)
    except ValueError:
        return None
    return dt

def _parse_common(text):
    """
    Parse common human-friendly date/time strings like:
    - 'Jan 2 2003 4:05 PM'
    - '2 Jan 2003 16:05'
    - '2003-01-02 16:05:00'
    - '2003/01/02 16:05'
    - 'Jan 2, 2003'
    - '2 Jan 2003'
    - '2003 Jan 2'
    - '4:05 PM'
    - '16:05'
    - 'today', 'now'
    """
    text = text.strip()
    lower = text.lower()

    if lower in ('now', 'today'):
        now = datetime.datetime.now(tz.UTC)
        if lower == 'today':
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        return now

    # Try to parse ISO8601 first
    dt = _parse_iso8601(text)
    if dt:
        return dt

    # Try to parse common formats with regex
    # Patterns:
    # 1) MonthName Day Year [time]
    # 2) Day MonthName Year [time]
    # 3) Year MonthName Day [time]
    # 4) Date with slashes or dashes
    # 5) Time only
    # 6) Date only

    # Extract time part if present
    time_part = None
    date_part = text
    time_match = re.search(r'(\d{1,2}:\d{2}(:\d{2})?(\.\d+)?\s*(AM|PM|am|pm)?)$', text)
    if time_match:
        time_part = time_match.group(1)
        date_part = text[:time_match.start()].strip()

    # Parse time
    hour = 0
    minute = 0
    second = 0
    microsecond = 0
    if time_part:
        # Parse time with optional AM/PM
        time_re = re.compile(r'(\d{1,2}):(\d{2})(?::(\d{2})(?:\.(\d+))?)?\s*(AM|PM|am|pm)?')
        m = time_re.match(time_part)
        if m:
            hour = int(m.group(1))
            minute = int(m.group(2))
            if m.group(3):
                second = int(m.group(3))
            if m.group(4):
                ms = m.group(4)[:6].ljust(6, '0')
                microsecond = int(ms)
            ampm = m.group(5)
            if ampm:
                ampm = ampm.lower()
                if ampm == 'pm' and hour != 12:
                    hour += 12
                elif ampm == 'am' and hour == 12:
                    hour = 0

    # Parse date_part
    # Try MonthName Day Year
    m = re.match(r'^(?P<month>[A-Za-z]{3,9})[ ,\-\.]+(?P<day>\d{1,2})(?:[ ,\-\.]+(?P<year>\d{4}))?$', date_part)
    if m:
        month = _months.get(m.group('month')[:3].lower())
        day = int(m.group('day'))
        year = int(m.group('year')) if m.group('year') else datetime.datetime.now().year
        try:
            return datetime.datetime(year, month, day, hour, minute, second, microsecond)
        except ValueError:
            pass

    # Try Day MonthName Year
    m = re.match(r'^(?P<day>\d{1,2})[ ,\-\.]+(?P<month>[A-Za-z]{3,9})(?:[ ,\-\.]+(?P<year>\d{4}))?$', date_part)
    if m:
        month = _months.get(m.group('month')[:3].lower())
        day = int(m.group('day'))
        year = int(m.group('year')) if m.group('year') else datetime.datetime.now().year
        try:
            return datetime.datetime(year, month, day, hour, minute, second, microsecond)
        except ValueError:
            pass

    # Try Year MonthName Day
    m = re.match(r'^(?P<year>\d{4})[ ,\-\.]+(?P<month>[A-Za-z]{3,9})[ ,\-\.]+(?P<day>\d{1,2})$', date_part)
    if m:
        year = int(m.group('year'))
        month = _months.get(m.group('month')[:3].lower())
        day = int(m.group('day'))
        try:
            return datetime.datetime(year, month, day, hour, minute, second, microsecond)
        except ValueError:
            pass

    # Try numeric date formats: YYYY-MM-DD, YYYY/MM/DD, DD-MM-YYYY, DD/MM/YYYY
    m = re.match(r'^(?P<y>\d{4})[-/](?P<m>\d{1,2})[-/](?P<d>\d{1,2})$', date_part)
    if m:
        try:
            return datetime.datetime(int(m.group('y')), int(m.group('m')), int(m.group('d')), hour, minute, second, microsecond)
        except ValueError:
            pass

    m = re.match(r'^(?P<d>\d{1,2})[-/](?P<m>\d{1,2})[-/](?P<y>\d{4})$', date_part)
    if m:
        try:
            return datetime.datetime(int(m.group('y')), int(m.group('m')), int(m.group('d')), hour, minute, second, microsecond)
        except ValueError:
            pass

    # Try time only
    if not date_part and time_part:
        now = datetime.datetime.now()
        return datetime.datetime(now.year, now.month, now.day, hour, minute, second, microsecond)

    # Try date only with no time
    m = re.match(r'^(?P<year>\d{4})$', date_part)
    if m:
        return datetime.datetime(int(m.group('year')), 1, 1)

    # If all fails, raise ValueError
    raise ValueError(f"Unknown string format: {text}")

def parse(timestr, tzinfos=None, **kwargs):
    """
    Parse a string into a datetime object.

    tzinfos is ignored except for tz.UTC and tz.gettz compatibility.

    Returns a datetime.datetime object, possibly tz-aware.
    """
    dt = _parse_common(timestr)
    # If tzinfos is provided, try to apply tzinfo if naive
    if tzinfos and dt.tzinfo is None:
        # tzinfos can be dict or callable, but we only support dict here
        if isinstance(tzinfos, dict):
            # Try to find tzinfo by name in string
            for name, tzinfo in tzinfos.items():
                if name in timestr:
                    dt = dt.replace(tzinfo=tzinfo)
                    break
        elif callable(tzinfos):
            # Call tzinfos with tzname
            # Extract tzname from string (simple heuristic)
            tzname = None
            m = re.search(r'\b([A-Za-z]{2,5})\b', timestr)
            if m:
                tzname = m.group(1)
            if tzname:
                tzinfo = tzinfos(tzname)
                if tzinfo:
                    dt = dt.replace(tzinfo=tzinfo)
    return dt