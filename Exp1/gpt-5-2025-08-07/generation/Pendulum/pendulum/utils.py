import datetime as _dt
import re
from typing import Optional, Tuple

from .timezone import timezone as tz_factory, FixedOffset, UTC


def ensure_timezone(tz):
    """
    Normalize tz argument into tzinfo or None.
    """
    if tz is None:
        return None
    if isinstance(tz, _dt.tzinfo):
        return tz
    if isinstance(tz, str):
        return tz_factory(tz)
    raise TypeError("tz must be a tzinfo, string, or None")


def days_in_month(year: int, month: int) -> int:
    """
    Returns the number of days in a given month/year.
    """
    if month == 12:
        next_month = _dt.date(year + 1, 1, 1)
    else:
        next_month = _dt.date(year, month + 1, 1)
    this_month = _dt.date(year, month, 1)
    return (next_month - this_month).days


_ISO_RE = re.compile(
    r"""
    ^
    (?P<year>\d{4})
    -(?P<month>\d{2})
    -(?P<day>\d{2})
    (?:[T\s]
        (?P<hour>\d{2})
        :
        (?P<minute>\d{2})
        (?:
            :
            (?P<second>\d{2})
            (?:
                \.
                (?P<fraction>\d{1,6})
            )?
        )?
    )?
    (?P<tz>
        Z|
        [+\-]\d{2}:\d{2}|
        [+\-]\d{2}\d{2}|
        [+\-]\d{2}
    )?
    $
    """,
    re.VERBOSE,
)


def parse_iso8601(text: str) -> Tuple[_dt.datetime, Optional[_dt.tzinfo]]:
    """
    Parse a subset of ISO-8601 and return (naive_datetime, tzinfo or None).
    The returned datetime will be naive; tzinfo returned separately if present,
    except 'Z' which returns UTC tzinfo.

    Examples:
      - '2020-01-01'
      - '2020-01-01T12:30'
      - '2020-01-01T12:30:45.123456Z'
      - '2020-01-01 12:30:45+02:00'
    """
    m = _ISO_RE.match(text)
    if not m:
        raise ValueError(f"Invalid ISO-8601 string: {text}")

    year = int(m.group("year"))
    month = int(m.group("month"))
    day = int(m.group("day"))
    hour = int(m.group("hour") or 0)
    minute = int(m.group("minute") or 0)
    second = int(m.group("second") or 0)
    fraction = m.group("fraction")
    microsecond = 0
    if fraction:
        if len(fraction) > 6:
            fraction = fraction[:6]
        microsecond = int(fraction.ljust(6, "0"))

    tztext = m.group("tz")
    tzinfo = None
    if tztext:
        if tztext == "Z":
            tzinfo = UTC
        else:
            # Normalize to +HH:MM
            if re.fullmatch(r"[+\-]\d{2}\d{2}", tztext):
                tztext = tztext[:3] + ":" + tztext[3:]
            elif re.fullmatch(r"[+\-]\d{2}", tztext):
                tztext = tztext + ":00"
            # parse offset
            sign = 1 if tztext[0] == "+" else -1
            hh = int(tztext[1:3])
            mm = int(tztext[4:6])
            minutes = sign * (hh * 60 + mm)
            tzinfo = FixedOffset(minutes)

    dt = _dt.datetime(year, month, day, hour, minute, second, microsecond)
    return dt, tzinfo