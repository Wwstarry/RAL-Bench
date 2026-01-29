from __future__ import annotations

import re
import datetime as _dt
from datetime import tzinfo

from .timezone import UTC, timezone as _timezone

_ISO_RE = re.compile(
    r"^"
    r"(?P<y>\d{4})-(?P<mo>\d{2})-(?P<d>\d{2})"
    r"(?:"
    r"(?:[Tt ](?P<h>\d{2}):(?P<mi>\d{2})"
    r"(?::(?P<s>\d{2})(?:\.(?P<f>\d{1,6}))?)?"
    r")"
    r"(?P<tz>Z|[+-]\d{2}(?::?\d{2})?)?"
    r")?"
    r"$"
)


def is_timezone(value) -> bool:
    return isinstance(value, _dt.tzinfo) and callable(getattr(value, "utcoffset", None))


def days_in_month(year: int, month: int) -> int:
    if month < 1 or month > 12:
        raise ValueError("month must be in 1..12")
    if month == 12:
        next_month = _dt.date(year + 1, 1, 1)
    else:
        next_month = _dt.date(year, month + 1, 1)
    this_month = _dt.date(year, month, 1)
    return (next_month - this_month).days


def add_months(dt: _dt.datetime, months: int):
    if not isinstance(months, int):
        raise TypeError("months must be int")

    y = dt.year
    m = dt.month + months
    # normalize year/month
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    d = min(dt.day, days_in_month(y, m))
    return dt.replace(year=y, month=m, day=d)


def add_years(dt: _dt.datetime, years: int):
    if not isinstance(years, int):
        raise TypeError("years must be int")
    y = dt.year + years
    m = dt.month
    d = min(dt.day, days_in_month(y, m))
    return dt.replace(year=y, month=m, day=d)


def _parse_tzinfo(tztext: str | None) -> tzinfo | None:
    if tztext is None:
        return None
    if tztext == "Z":
        return UTC
    # Delegate fixed offset parsing to pendulum.timezone()
    return _timezone(tztext)


def parse_iso8601(text: str, tz: str | tzinfo | None = None, strict: bool = True):
    from .datetime import DateTime  # local import to avoid cycle

    if not isinstance(text, str):
        raise TypeError("text must be str")

    s = text.strip()
    m = _ISO_RE.match(s)
    if not m:
        raise ValueError(f"Invalid ISO-8601 string: {text!r}")

    year = int(m.group("y"))
    month = int(m.group("mo"))
    day = int(m.group("d"))

    if m.group("h") is None:
        hour = minute = second = microsecond = 0
        tzinfo = None
    else:
        hour = int(m.group("h"))
        minute = int(m.group("mi"))
        second = int(m.group("s") or "0")
        frac = m.group("f")
        if frac:
            microsecond = int(frac.ljust(6, "0"))
        else:
            microsecond = 0
        tzinfo = _parse_tzinfo(m.group("tz"))

    if tzinfo is not None:
        # Explicit offset/Z wins over tz parameter.
        return DateTime(year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)

    # No explicit tz in string
    if tz is None:
        tzinfo = UTC
    else:
        tzinfo = _timezone(tz)

    return DateTime(year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)