# Minimal pure-Python Pendulum-like API

from .datetime import DateTime
from .timezone import timezone as _timezone, FixedOffset, UTC
from .duration import Duration
from .utils import ensure_timezone
from .formatting import humanize_duration
from .utils import parse_iso8601


def timezone(name_or_offset):
    """
    Returns a tzinfo for the given timezone name or offset string.

    Examples:
    - pendulum.timezone('UTC')
    - pendulum.timezone('Europe/Paris')
    - pendulum.timezone('+02:00')
    """
    return _timezone(name_or_offset)


def datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0, tz=None):
    """
    Create a timezone-aware or naive DateTime.
    tz can be:
      - None (naive)
      - a string timezone name or offset (e.g. 'UTC', 'Europe/Paris', '+02:00')
      - a tzinfo instance
    """
    tzinfo = ensure_timezone(tz)
    return DateTime(year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)


def now(tz=None):
    """
    Returns the current time as a DateTime optionally in the provided timezone.
    """
    tzinfo = ensure_timezone(tz)
    return DateTime.now(tzinfo)


def parse(text, tz=None):
    """
    Parse an ISO-8601-like string into a DateTime.

    Supports:
    - 'YYYY-MM-DD'
    - 'YYYY-MM-DDTHH:MM[:SS[.ffffff]]'
    - Timezone offsets: 'Z', '+HH:MM', '+HHMM', '+HH', '-HH:MM', etc

    If tz is provided and the string contains an offset, the result is converted
    to the provided timezone. If tz is provided and the string does not contain an
    offset, the result is assumed to be in the provided timezone.
    """
    tzinfo = ensure_timezone(tz)
    dt, parsed_tz = parse_iso8601(text)

    if parsed_tz is not None:
        # Aware datetime from parsed offset/name
        result = DateTime.from_datetime(dt.replace(tzinfo=parsed_tz))
        if tzinfo is not None and tzinfo is not parsed_tz:
            return result.in_timezone(tzinfo)
        return result
    else:
        # No offset in string
        if tzinfo is not None:
            return DateTime.from_datetime(dt.replace(tzinfo=tzinfo))
        return DateTime.from_datetime(dt)  # naive

def duration(
    years=0,
    months=0,
    weeks=0,
    days=0,
    hours=0,
    minutes=0,
    seconds=0,
    microseconds=0,
):
    """
    Create a Duration. For simplicity, years and months are approximated:
      - 1 year = 365 days
      - 1 month = 30 days
    This approximates Pendulum's behavior for many common test cases but does
    not carry calendar-aware months/years. If exact calendar periods are needed,
    use DateTime.add(years=..., months=...) on DateTime.
    """
    total_days = days + weeks * 7 + years * 365 + months * 30
    total_seconds = seconds + minutes * 60 + hours * 3600
    return Duration(days=total_days, seconds=total_seconds, microseconds=microseconds)