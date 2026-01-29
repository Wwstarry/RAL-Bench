from __future__ import annotations

from datetime import tzinfo as _tzinfo

from .datetime import DateTime
from .duration import Duration
from .timezone import UTC, local_timezone, timezone
from .utils import parse_iso8601


def datetime(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    microsecond: int = 0,
    tz: str | _tzinfo | None = "UTC",
) -> DateTime:
    """
    Create a DateTime. Defaults to UTC-aware unless tz=None is explicitly passed.
    """
    tzinfo = None if tz is None else timezone(tz)
    return DateTime(year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)


def parse(text: str, tz: str | _tzinfo | None = None, strict: bool = True) -> DateTime:
    return parse_iso8601(text, tz=tz, strict=strict)


def now(tz: str | _tzinfo | None = None) -> DateTime:
    if tz is None:
        tzinfo = local_timezone()
    else:
        tzinfo = timezone(tz)
    return DateTime.now(tzinfo)  # type: ignore[arg-type]


def duration(
    years: int = 0,
    months: int = 0,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    microseconds: int = 0,
) -> Duration:
    return Duration(
        years=years,
        months=months,
        weeks=weeks,
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        microseconds=microseconds,
    )


__all__ = [
    "DateTime",
    "Duration",
    "UTC",
    "datetime",
    "duration",
    "local_timezone",
    "now",
    "parse",
    "timezone",
]