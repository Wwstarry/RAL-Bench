import re
from datetime import datetime, date, time, timedelta
from dateutil.tz import gettz, UTC

_ISO_REGEX = re.compile(
    r"""
    ^
    (?P<year>\d{4})
    (?:-(?P<month>\d{2})
        (?:-(?P<day>\d{2})
            (?:[T\s](?P<hour>\d{2})
                :(?P<minute>\d{2})
                (?::(?P<second>\d{2})
                    (?:\.(?P<microsecond>\d{1,6}))?
                )?
                (?P<tzinfo>Z|[+-]\d{2}:?\d{2})?
            )?
        )?
    )?
    $
    """,
    re.VERBOSE,
)

# Common formats for human-friendly dates
_COMMON_FORMATS = [
    # "YYYY-MM-DD HH:MM:SS"
    re.compile(
        r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})[ T](?P<hour>\d{2}):(?P<minute>\d{2})(:(?P<second>\d{2}))?(?P<tzinfo>Z|[+-]\d{2}:?\d{2})?$"
    ),
    # "YYYY/MM/DD HH:MM"
    re.compile(
        r"^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})[ T](?P<hour>\d{2}):(?P<minute>\d{2})(?P<tzinfo>Z|[+-]\d{2}:?\d{2})?$"
    ),
    # "DD MMM YYYY HH:MM:SS"
    re.compile(
        r"^(?P<day>\d{1,2}) (?P<month_name>[A-Za-z]+) (?P<year>\d{4})[ T](?P<hour>\d{2}):(?P<minute>\d{2})(:(?P<second>\d{2}))?(?P<tzinfo>Z|[+-]\d{2}:?\d{2})?$"
    ),
    # "YYYY-MM-DD"
    re.compile(
        r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})(?P<tzinfo>Z|[+-]\d{2}:?\d{2})?$"
    ),
    # "YYYY/MM/DD"
    re.compile(
        r"^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})(?P<tzinfo>Z|[+-]\d{2}:?\d{2})?$"
    ),
]

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

def _parse_tzinfo(tzstr):
    if tzstr is None:
        return None
    if tzstr == "Z":
        return UTC
    m = re.match(r"([+-])(\d{2}):?(\d{2})", tzstr)
    if m:
        sign = 1 if m.group(1) == "+" else -1
        hours = int(m.group(2))
        minutes = int(m.group(3))
        offset = timedelta(hours=hours, minutes=minutes) * sign
        from dateutil.tz import tzoffset
        return tzoffset(None, offset.total_seconds())
    return gettz(tzstr)

def parse(timestr, default=None, ignoretz=False, tzinfos=None, **kwargs):
    """
    Parse a string into a datetime object.
    Supports ISO-8601 and common human-friendly formats.
    """
    timestr = timestr.strip()
    m = _ISO_REGEX.match(timestr)
    if m:
        gd = m.groupdict()
        year = int(gd.get("year"))
        month = int(gd.get("month") or 1)
        day = int(gd.get("day") or 1)
        hour = int(gd.get("hour") or 0)
        minute = int(gd.get("minute") or 0)
        second = int(gd.get("second") or 0)
        microsecond = int((gd.get("microsecond") or "0").ljust(6, "0"))
        tzinfo = None if ignoretz else _parse_tzinfo(gd.get("tzinfo"))
        return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)
    # Try common formats
    for regex in _COMMON_FORMATS:
        m = regex.match(timestr)
        if m:
            gd = m.groupdict()
            year = int(gd.get("year"))
            if gd.get("month"):
                month = int(gd.get("month"))
            elif gd.get("month_name"):
                month = _MONTHS[gd.get("month_name").lower()[:3]]
            else:
                month = 1
            day = int(gd.get("day") or 1)
            hour = int(gd.get("hour") or 0)
            minute = int(gd.get("minute") or 0)
            second = int(gd.get("second") or 0)
            tzinfo = None if ignoretz else _parse_tzinfo(gd.get("tzinfo"))
            return datetime(year, month, day, hour, minute, second, tzinfo=tzinfo)
    # Fallback: try to parse RFC 2822 (e.g. "Mon, 21 Jun 2021 10:00:00 +0000")
    m = re.match(
        r"^(?:[A-Za-z]{3}, )?(?P<day>\d{1,2}) (?P<month_name>[A-Za-z]+) (?P<year>\d{4}) (?P<hour>\d{2}):(?P<minute>\d{2})(:(?P<second>\d{2}))? (?P<tzinfo>Z|[+-]\d{2}:?\d{2})?$",
        timestr,
    )
    if m:
        gd = m.groupdict()
        year = int(gd.get("year"))
        month = _MONTHS[gd.get("month_name").lower()[:3]]
        day = int(gd.get("day"))
        hour = int(gd.get("hour") or 0)
        minute = int(gd.get("minute") or 0)
        second = int(gd.get("second") or 0)
        tzinfo = None if ignoretz else _parse_tzinfo(gd.get("tzinfo"))
        return datetime(year, month, day, hour, minute, second, tzinfo=tzinfo)
    # Fallback: try datetime.fromisoformat (Python 3.7+)
    try:
        dt = datetime.fromisoformat(timestr)
        if ignoretz:
            return dt.replace(tzinfo=None)
        return dt
    except Exception:
        pass
    raise ValueError(f"Unknown datetime format: {timestr}")