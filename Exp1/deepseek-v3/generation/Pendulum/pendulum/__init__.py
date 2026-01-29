from .datetime import DateTime
from .timezone import Timezone, FixedTimezone
from .duration import Duration
from .formatting import diff_for_humans
import pytz

def datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0, tz=None):
    return DateTime(year, month, day, hour, minute, second, microsecond, tz=tz)

def parse(text, tz=None):
    return DateTime.parse(text, tz=tz)

def timezone(name):
    return Timezone(name)

def duration(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
    return Duration(days=days, seconds=seconds, microseconds=microseconds,
                   milliseconds=milliseconds, minutes=minutes, hours=hours,
                   weeks=weeks)

def now(tz=None):
    return DateTime.now(tz=tz)

def utcnow():
    return DateTime.utcnow()

# Expose main classes
DateTime = DateTime
Timezone = Timezone
FixedTimezone = FixedTimezone
Duration = Duration

__all__ = [
    'DateTime', 'Timezone', 'FixedTimezone', 'Duration',
    'datetime', 'parse', 'timezone', 'duration', 'now', 'utcnow'
]