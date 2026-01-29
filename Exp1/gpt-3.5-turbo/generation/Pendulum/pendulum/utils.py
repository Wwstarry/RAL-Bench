import re
from datetime import datetime as _datetime, timedelta as _timedelta
from .timezone import timezone, Timezone

_iso8601_regex = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})"  # date
    r"(?:[T\s](\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?)?"  # time and optional microseconds
    r"(Z|[+-]\d{2}:?\d{2})?$"  # timezone
)

def _parse_iso8601_datetime(dt_str):
    """
    Parse an ISO8601 datetime string and return (datetime.datetime, timezone or None)
    """
    m = _iso8601_regex.match(dt_str)
    if not m:
        raise ValueError(f"Invalid ISO8601 datetime string: {dt_str}")

    year, month, day, hour, minute, second, microsecond, tz_str = m.groups()

    year = int(year)
    month = int(month)
    day = int(day)
    hour = int(hour) if hour is not None else 0
    minute = int(minute) if minute is not None else 0
    second = int(second) if second is not None else 0
    if microsecond:
        microsecond = int(microsecond.ljust(6, '0'))
    else:
        microsecond = 0

    dt = _datetime(year, month, day, hour, minute, second, microsecond)

    tz = None
    if tz_str is None:
        tz = None
    elif tz_str == "Z":
        tz = timezone("UTC")
    else:
        # tz_str like +HH:MM or -HHMM or +HHMM
        tz = timezone(tz_str)

    return dt, tz