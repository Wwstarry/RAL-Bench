"""
Pendulum - A pure Python datetime and timezone utility library.
"""

from pendulum.datetime import DateTime
from pendulum.duration import Duration
from pendulum.timezone import Timezone, timezone
from pendulum.utils import parse


__version__ = "3.0.0"


def datetime(
    year,
    month,
    day,
    hour=0,
    minute=0,
    second=0,
    microsecond=0,
    tz=None,
    fold=0,
):
    """
    Create a new DateTime instance.
    
    Args:
        year: Year
        month: Month (1-12)
        day: Day (1-31)
        hour: Hour (0-23)
        minute: Minute (0-59)
        second: Second (0-59)
        microsecond: Microsecond (0-999999)
        tz: Timezone (string, Timezone object, or None for UTC)
        fold: Fold value for ambiguous times (0 or 1)
    
    Returns:
        DateTime: A new DateTime instance
    """
    return DateTime(
        year, month, day, hour, minute, second, microsecond, tz=tz, fold=fold
    )


def duration(
    days=0,
    seconds=0,
    microseconds=0,
    milliseconds=0,
    minutes=0,
    hours=0,
    weeks=0,
    years=0,
    months=0,
):
    """
    Create a new Duration instance.
    
    Args:
        days: Number of days
        seconds: Number of seconds
        microseconds: Number of microseconds
        milliseconds: Number of milliseconds
        minutes: Number of minutes
        hours: Number of hours
        weeks: Number of weeks
        years: Number of years
        months: Number of months
    
    Returns:
        Duration: A new Duration instance
    """
    return Duration(
        days=days,
        seconds=seconds,
        microseconds=microseconds,
        milliseconds=milliseconds,
        minutes=minutes,
        hours=hours,
        weeks=weeks,
        years=years,
        months=months,
    )


def now(tz=None):
    """
    Get the current date and time.
    
    Args:
        tz: Timezone (string, Timezone object, or None for UTC)
    
    Returns:
        DateTime: Current DateTime instance
    """
    return DateTime.now(tz=tz)


def today(tz=None):
    """
    Get today's date at midnight.
    
    Args:
        tz: Timezone (string, Timezone object, or None for UTC)
    
    Returns:
        DateTime: Today's DateTime instance at midnight
    """
    return DateTime.today(tz=tz)


def yesterday(tz=None):
    """
    Get yesterday's date at midnight.
    
    Args:
        tz: Timezone (string, Timezone object, or None for UTC)
    
    Returns:
        DateTime: Yesterday's DateTime instance at midnight
    """
    return DateTime.yesterday(tz=tz)


def tomorrow(tz=None):
    """
    Get tomorrow's date at midnight.
    
    Args:
        tz: Timezone (string, Timezone object, or None for UTC)
    
    Returns:
        DateTime: Tomorrow's DateTime instance at midnight
    """
    return DateTime.tomorrow(tz=tz)


__all__ = [
    "DateTime",
    "Duration",
    "Timezone",
    "datetime",
    "duration",
    "now",
    "parse",
    "timezone",
    "today",
    "tomorrow",
    "yesterday",
]