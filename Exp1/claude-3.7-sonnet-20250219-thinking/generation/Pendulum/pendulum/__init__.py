import datetime as dt
from typing import Union, Optional

from .datetime import DateTime
from .timezone import Timezone
from .duration import Duration
from .formatting import parse_iso8601

def datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0, tz=None):
    """Create a new DateTime instance."""
    return DateTime(year, month, day, hour, minute, second, microsecond, tz=tz)

def now(tz=None):
    """Get the current DateTime."""
    return DateTime.now(tz=tz)

def today(tz=None):
    """Get the current date as DateTime."""
    return now(tz=tz).start_of('day')

def tomorrow(tz=None):
    """Get tomorrow as DateTime."""
    return today(tz=tz).add(days=1)

def yesterday(tz=None):
    """Get yesterday as DateTime."""
    return today(tz=tz).add(days=-1)

def parse(text, tz=None):
    """Parse a datetime string."""
    return parse_iso8601(text, tz)

def timezone(name):
    """Get a timezone instance."""
    return Timezone.instance(name)

def duration(
    years=0, months=0, weeks=0, days=0, hours=0, minutes=0, seconds=0, microseconds=0
):
    """Create a Duration instance."""
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

def from_timestamp(timestamp, tz=None):
    """Create a DateTime from a timestamp."""
    return DateTime.fromtimestamp(timestamp, tz=tz)

# Export public API
__all__ = [
    'DateTime', 'Timezone', 'Duration',
    'datetime', 'now', 'today', 'tomorrow', 'yesterday',
    'parse', 'timezone', 'duration', 'from_timestamp'
]