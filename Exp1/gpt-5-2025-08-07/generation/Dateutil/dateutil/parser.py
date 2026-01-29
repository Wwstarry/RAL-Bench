import re
from datetime import datetime, date, time, timedelta, timezone
from email.utils import parsedate_to_datetime

try:
    # Python 3.11+ supports fromisoformat with 'Z'
    _Z_SUPPORT = True
except Exception:
    _Z_SUPPORT = False


class ParserError(ValueError):
    pass


# Common timezone abbreviation table to fixed offsets (in minutes)
# Note: Abbreviations are ambiguous in reality; here we provide a pragmatic subset.
_ABBR_OFFSETS_MIN = {
    "UTC": 0,
    "UT": 0,
    "GMT": 0,
    "Z": 0,
    "EST": -5 * 60,
    "EDT": -4 * 60,
    "CST": -6 * 60,
    "CDT": -5 * 60,
    "MST": -7 * 60,
    "MDT": -6 * 60,
    "PST": -8 * 60,
    "PDT": -7 * 60,
    "CET": 1 * 60,
    "CEST": 2 * 60,
    "EET": 2 * 60,
    "EEST": 3 * 60,
    "WET": 0,
    "WEST": 1 * 60,
    "BST": 1 * 60,
    "IST": 5 * 60 + 30,  # India Standard Time
}

_MONTHS = {
    "JANUARY": 1, "JAN": 1,
    "FEBRUARY": 2, "FEB": 2,
    "MARCH": 3, "MAR": 3,
    "APRIL": 4, "APR": 4,
    "MAY": 5,
    "JUNE": 6, "JUN": 6,
    "JULY": 7, "JUL": 7,
    "AUGUST": 8, "AUG": 8,
    "SEPTEMBER": 9, "SEP": 9, "SEPT": 9,
    "OCTOBER": 10, "OCT": 10,
    "NOVEMBER": 11, "NOV": 11,
    "DECEMBER": 12, "DEC": 12,
}


def _parse_offset(tzstr):
    """
    Parse timezone offset strings like +HH:MM, -HHMM, +HH into a datetime.timezone.
    Returns a timezone or None if not a valid offset string.
    """
    tzstr = tzstr.strip()
    m = re.match(r'^([+\-])(\d{2}):?(\d{2})?$', tzstr)
    if m:
        sign = 1 if m.group(1) == '+' else -1
        hours = int(m.group(2))
        minutes = int(m.group(3) or "0")
        offset = timedelta(hours=hours, minutes=minutes) * sign
        return timezone(offset)
    # Also allow +HHMMSS or +HHMM
    m2 = re.match(r'^([+\-])(\d{2})(\d{2})(\d{2})?$', tzstr)
    if m2:
        sign = 1 if m2.group(1) == '+' else -1
        hours = int(m2.group(2))
        minutes = int(m2.group(3))
        seconds = int(m2.group(4) or "0")
        offset = timedelta(hours=hours, minutes=minutes, seconds=seconds) * sign
        return timezone(offset)
    return None


def _get_tzinfo_from_token(token, tzinfos=None):
    """
    Resolve a time zone token into tzinfo using tzinfos mapping/callable or
    abbreviation table and offset parsing.
    """
    if not token:
        return None

    # If tzinfos provided
    if tzinfos is not None:
        if callable(tzinfos):
            res = tzinfos(token)
        else:
            res = tzinfos.get(token)
        if res is not None:
            if isinstance(res, int):
                return timezone(timedelta(seconds=res))
            if isinstance(res, timedelta):
                return timezone(res)
            # Assume tzinfo
            return res

    # Zulu 'Z'
    if token.upper() == 'Z':
        return timezone.utc

    # Numeric offset strings
    tz = _parse_offset(token)
    if tz:
        return tz

    # Abbreviations
    abbr = token.upper()
    if abbr in _ABBR_OFFSETS_MIN:
        minutes = _ABBR_OFFSETS_MIN[abbr]
        return timezone(timedelta(minutes=minutes))

    # Anything else, try using dateutil.tz.gettz if available
    try:
        from . import tz as _tzmod
        tzinfo = _tzmod.gettz(token)
        return tzinfo
    except Exception:
        return None


def _combine(dt_parts, time_parts, tzinfo=None, default=None):
    """
    Combine date and time parts into datetime, using default to fill missing components.
    """
    if dt_parts is None and default is None:
        raise ParserError("Unable to parse date")

    if default is None:
        default = datetime(1900, 1, 1)

    year = dt_parts[0] if dt_parts else default.year
    month = dt_parts[1] if dt_parts else default.month
    day = dt_parts[2] if dt_parts else default.day

    hour = time_parts[0] if time_parts else default.hour
    minute = time_parts[1] if time_parts else default.minute
    second = time_parts[2] if time_parts else default.second
    microsecond = time_parts[3] if time_parts and len(time_parts) > 3 else default.microsecond

    try:
        return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)
    except Exception as e:
        raise ParserError(str(e))


def _try_email_parser(s):
    try:
        dt = parsedate_to_datetime(s)
        return dt
    except Exception:
        return None


def parse(timestr, dayfirst=False, yearfirst=False, tzinfos=None, default=None, fuzzy=False):
    """
    Flexible datetime string parser.

    Supports:
    - ISO-8601 dates and datetimes (YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS[.fff][Z|+HH:MM])
    - RFC 2822 / email-style dates via email.utils.parsedate_to_datetime
    - Common human-friendly formats: "January 2, 2003 4:05 PM", "Jan 2 2003", "1/2/2003"
    - Time zone offsets and common abbreviations (UTC, GMT, EST, EDT, etc.)
    """
    if not isinstance(timestr, str):
        raise ParserError("Input must be a string")

    s = timestr.strip()

    # Try email/RFC parser first
    dt = _try_email_parser(s)
    if dt:
        return dt

    # ISO-8601 (including 'Z' or +/- offsets)
    # We'll try datetime.fromisoformat for most variants
    iso_candidate = s
    if s.endswith('Z'):
        # Python's fromisoformat before 3.11 can't parse 'Z'; replace with +00:00
        iso_candidate = s[:-1] + '+00:00'
    try:
        dt = datetime.fromisoformat(iso_candidate)
        # fromisoformat cannot parse space-separated timezone like " ... GMT"
        # but above would have returned None; If parsed, return
        return dt
    except Exception:
        pass

    # Manual ISO regex: YYYY-MM-DD [T| ] HH:MM[:SS[.us]] [Z|+HH[:MM]|+HHMM]
    iso_re = re.compile(
        r'^\s*(\d{4})(?:-(\d{2})(?:-(\d{2}))?)'
        r'(?:[T\s](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,6}))?)?)?'
        r'(?:\s*(Z|[+\-]\d{2}:?\d{2}|[+\-]\d{2})\s*)?$'
    )
    m = iso_re.match(s)
    if m:
        y = int(m.group(1))
        mth = int(m.group(2)) if m.group(2) else 1
        d = int(m.group(3)) if m.group(3) else 1
        hh = int(m.group(4)) if m.group(4) else 0
        mm = int(m.group(5)) if m.group(5) else 0
        ss = int(m.group(6)) if m.group(6) else 0
        us = m.group(7)
        us = int((us or "0").ljust(6, '0')) if us else 0
        tz_token = m.group(8)
        tzinfo = _get_tzinfo_from_token(tz_token, tzinfos=tzinfos)
        try:
            return datetime(y, mth, d, hh, mm, ss, us, tzinfo=tzinfo)
        except Exception as e:
            raise ParserError(str(e))

    # Human-friendly formats:
    # 1) "Monthname D, YYYY [time]" or "Monthname D YYYY [time]"
    human_re = re.compile(
        r'^\s*([A-Za-z]+)\s+(\d{1,2})(?:,)?\s+(\d{4})'
        r'(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM|am|pm)?)?'
        r'(?:\s*(\w{1,5}))?\s*$'
    )
    m = human_re.match(s)
    if m:
        mon_str = m.group(1).upper()
        mon = _MONTHS.get(mon_str)
        if not mon:
            raise ParserError("Unknown month name: %s" % m.group(1))
        day = int(m.group(2))
        year = int(m.group(3))
        hh = int(m.group(4) or 0)
        mm = int(m.group(5) or 0)
        ss = int(m.group(6) or 0)
        ampm = m.group(7)
        tz_token = m.group(8)

        if ampm:
            ampm = ampm.lower()
            if ampm == 'pm' and hh < 12:
                hh += 12
            elif ampm == 'am' and hh == 12:
                hh = 0

        tzinfo = _get_tzinfo_from_token(tz_token, tzinfos=tzinfos)
        try:
            return datetime(year, mon, day, hh, mm, ss, tzinfo=tzinfo)
        except Exception as e:
            raise ParserError(str(e))

    # 2) "Mon D YYYY [HH:MM[:SS] [TZ]]"
    human2_re = re.compile(
        r'^\s*([A-Za-z]+)\s+(\d{1,2})\s+(\d{4})'
        r'(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?'
        r'(?:\s*(\w{1,5}|[+\-]\d{2}:?\d{2}|Z))?\s*$'
    )
    m = human2_re.match(s)
    if m:
        mon_str = m.group(1).upper()
        mon = _MONTHS.get(mon_str)
        if mon:
            day = int(m.group(2))
            year = int(m.group(3))
            hh = int(m.group(4) or 0)
            mm = int(m.group(5) or 0)
            ss = int(m.group(6) or 0)
            tz_token = m.group(7)
            tzinfo = _get_tzinfo_from_token(tz_token, tzinfos=tzinfos)
            try:
                return datetime(year, mon, day, hh, mm, ss, tzinfo=tzinfo)
            except Exception as e:
                raise ParserError(str(e))

    # 3) "YYYY/MM/DD [HH:MM[:SS] [TZ]]" or "MM/DD/YYYY" or "DD/MM/YYYY" depending on dayfirst/yearfirst
    # Generic date + optional time
    date_time_re = re.compile(
        r'^\s*(\d{1,4})[\/\-](\d{1,2})[\/\-](\d{1,4})'
        r'(?:\s+(\d{1,2}):(\d{2})(?::(\d{2})(?:\.(\d{1,6}))?)?)?'
        r'(?:\s*(\w{1,5}|[+\-]\d{2}:?\d{2}|Z))?\s*$'
    )
    m = date_time_re.match(s)
    if m:
        a = int(m.group(1))
        b = int(m.group(2))
        c = int(m.group(3))
        hh = int(m.group(4) or 0)
        mm = int(m.group(5) or 0)
        ss = int(m.group(6) or 0)
        us = m.group(7)
        us = int((us or "0").ljust(6, '0')) if us else 0
        tz_token = m.group(8)
        tzinfo = _get_tzinfo_from_token(tz_token, tzinfos=tzinfos)

        # Decide ordering:
        if yearfirst:
            year, month, day = a, b, c
        else:
            if dayfirst:
                day, month, year = a, b, c
            else:
                month, day, year = a, b, c
        # Normalize year like 2-digit? We'll assume 4-digit or 1-4-digit exact
        if year < 100 and yearfirst:
            # naive pivot, assume 1900-1999 for < 100
            year += 1900
        try:
            return datetime(year, month, day, hh, mm, ss, us, tzinfo=tzinfo)
        except Exception as e:
            raise ParserError(str(e))

    # Fuzzy: remove trailing timezone token and retry basic patterns
    if fuzzy:
        # Remove any parentheses or trailing words
        cleaned = re.sub(r'\([^)]*\)', '', s)
        cleaned = re.sub(r'\s+[A-Za-z]{2,5}$', '', cleaned)
        try:
            return parse(cleaned, dayfirst=dayfirst, yearfirst=yearfirst, tzinfos=tzinfos, default=default, fuzzy=False)
        except ParserError:
            pass

    # Fall back: try only date portion "YYYY-MM-DD"
    m = re.match(r'^\s*(\d{4})-(\d{2})-(\d{2})\s*$', s)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception as e:
            raise ParserError(str(e))

    raise ParserError("Unknown string format: %r" % timestr)