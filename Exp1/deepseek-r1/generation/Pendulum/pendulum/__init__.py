import sys
from typing import Optional, Union, Any

from .datetime import DateTime
from .duration import Duration
from .timezone import Timezone, FixedTimezone
from .formatting import Formatter

__version__ = "1.0.0"
__all__ = [
    "datetime",
    "parse",
    "timezone",
    "duration",
    "now",
    "today",
    "yesterday",
    "tomorrow",
    "UTC",
    "DateTime",
    "Duration",
    "Timezone",
    "Formatter"
]

# Timezone constants
UTC = Timezone("UTC")

def datetime(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    microsecond: int = 0,
    tz: Optional[Union[str, Timezone]] = None,
    fold: int = 0
) -> DateTime:
    """Create a timezone-aware datetime."""
    return DateTime.create(
        year, month, day,
        hour, minute, second, microsecond,
        tz, fold
    )

def parse(
    text: str,
    tz: Optional[Union[str, Timezone]] = None,
    strict: bool = True
) -> DateTime:
    """Parse ISO-8601 string into a DateTime."""
    return DateTime.parse(text, tz, strict)

def timezone(name: str) -> Timezone:
    """Get a timezone by name."""
    return Timezone(name)

def duration(
    years: int = 0,
    months: int = 0,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    microseconds: int = 0
) -> Duration:
    """Create a Duration object."""
    return Duration(
        years=years,
        months=months,
        weeks=weeks,
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        microseconds=microseconds
    )

def now(tz: Optional[Union[str, Timezone]] = None) -> DateTime:
    """Get current datetime in specified timezone."""
    return DateTime.now(tz)

def today(tz: Optional[Union[str, Timezone]] = None) -> DateTime:
    """Get today's date at 00:00:00 in specified timezone."""
    return DateTime.today(tz)

def yesterday(tz: Optional[Union[str, Timezone]] = None) -> DateTime:
    """Get yesterday's date at 00:00:00 in specified timezone."""
    return DateTime.yesterday(tz)

def tomorrow(tz: Optional[Union[str, Timezone]] = None) -> DateTime:
    """Get tomorrow's date at 00:00:00 in specified timezone."""
    return DateTime.tomorrow(tz)

# Monkey-patch to make pendulum.datetime etc work
sys.modules[__name__].datetime = datetime
sys.modules[__name__].parse = parse
sys.modules[__name__].timezone = timezone
sys.modules[__name__].duration = duration
sys.modules[__name__].now = now
sys.modules[__name__].today = today
sys.modules[__name__].yesterday = yesterday
sys.modules[__name__].tomorrow = tomorrow