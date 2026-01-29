import re
from datetime import datetime as _dt, timezone as _timezone, timedelta

def isoformat(dt):
    # dt is a datetime object
    s = dt.strftime("%Y-%m-%dT%H:%M:%S")
    if dt.microsecond:
        s += f".{dt.microsecond:06d}"
    offset = dt.utcoffset()
    if offset is None or offset.total_seconds() == 0:
        s += "Z"
    else:
        total_seconds = int(offset.total_seconds())
        sign = "+" if total_seconds >= 0 else "-"
        total_seconds = abs(total_seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        s += f"{sign}{hours:02d}:{minutes:02d}"
    return s

def parse_iso8601(dt_str):
    # Returns (datetime, tzinfo or None)
    # Example: 2020-01-01T12:34:56Z, 2020-01-01T12:34:56+02:00
    iso_re = re.compile(
        r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
        r"[T ](?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
        r"(?:\.(?P<microsecond>\d{1,6}))?"
        r"(?P<tz>Z|[+-]\d{2}:\d{2})?$"
    )
    m = iso_re.match(dt_str)
    if not m:
        raise ValueError(f"Invalid ISO-8601 datetime string: {dt_str}")
    kw = {k: int(m.group(k)) for k in ["year", "month", "day", "hour", "minute", "second"]}
    micro = m.group("microsecond")
    if micro:
        kw["microsecond"] = int(micro.ljust(6, "0"))
    else:
        kw["microsecond"] = 0
    tz = m.group("tz")
    if tz == "Z":
        tzinfo = _timezone.utc
    elif tz and re.match(r"[+-]\d{2}:\d{2}", tz):
        sign = 1 if tz[0] == "+" else -1
        hours = int(tz[1:3])
        minutes = int(tz[4:6])
        offset = timedelta(hours=hours, minutes=minutes) * sign
        tzinfo = _timezone(offset)
    else:
        tzinfo = None
    dt = _dt(**kw, tzinfo=tzinfo)
    return dt, tzinfo