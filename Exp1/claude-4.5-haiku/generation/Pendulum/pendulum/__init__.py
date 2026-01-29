from pendulum.datetime import DateTime
from pendulum.timezone import Timezone
from pendulum.duration import Duration
from pendulum.parsing import parse
import datetime as _datetime

__version__ = "2.1.2"

_local_tz = None

def timezone(name):
    """Create a Timezone instance."""
    return Timezone(name)

def datetime(year, month=1, day=1, hour=0, minute=0, second=0, microsecond=0, tz=None):
    """Create a DateTime instance."""
    if tz is None:
        tz_obj = None
    elif isinstance(tz, str):
        tz_obj = Timezone(tz)
    elif isinstance(tz, Timezone):
        tz_obj = tz
    else:
        tz_obj = None
    
    return DateTime(year, month, day, hour, minute, second, microsecond, tzinfo=tz_obj)

def duration(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
    """Create a Duration instance."""
    return Duration(
        days=days,
        seconds=seconds,
        microseconds=microseconds,
        milliseconds=milliseconds,
        minutes=minutes,
        hours=hours,
        weeks=weeks
    )

def now(tz=None):
    """Get the current datetime."""
    if tz is None:
        tz_obj = None
    elif isinstance(tz, str):
        tz_obj = Timezone(tz)
    elif isinstance(tz, Timezone):
        tz_obj = tz
    else:
        tz_obj = None
    
    dt = _datetime.datetime.now(tz=tz_obj)
    return DateTime(
        dt.year, dt.month, dt.day,
        dt.hour, dt.minute, dt.second, dt.microsecond,
        tzinfo=tz_obj
    )

def today(tz=None):
    """Get today's date."""
    if tz is None:
        tz_obj = None
    elif isinstance(tz, str):
        tz_obj = Timezone(tz)
    elif isinstance(tz, Timezone):
        tz_obj = tz
    else:
        tz_obj = None
    
    dt = _datetime.datetime.today()
    return DateTime(
        dt.year, dt.month, dt.day,
        0, 0, 0, 0,
        tzinfo=tz_obj
    )

__all__ = [
    'DateTime',
    'Timezone',
    'Duration',
    'parse',
    'timezone',
    'datetime',
    'duration',
    'now',
    'today',
]