"""
Pendulum - Python datetime made easy
"""

from .datetime import DateTime
from .duration import Duration
from .timezone import Timezone, FixedTimezone
from .exceptions import PendulumException

import sys
import re
from datetime import datetime as _datetime
from datetime import timedelta
from typing import Optional, Union, Any, overload


__version__ = "1.0.0"
__all__ = [
    "DateTime",
    "Duration",
    "Timezone",
    "FixedTimezone",
    "PendulumException",
    "datetime",
    "parse",
    "now",
    "today",
    "tomorrow",
    "yesterday",
    "timezone",
    "duration",
    "from_timestamp",
    "set_locale",
    "get_locale",
    "set_formatter",
    "get_formatter",
    "week_starts_at",
    "week_ends_at",
    "TEST_MODE",
]


# Global settings
_TEST_MODE = False
_LOCALE = "en"
_WEEK_STARTS_AT = 0  # Monday
_WEEK_ENDS_AT = 6    # Sunday
_FORMATTER = None


def set_locale(locale: str) -> None:
    """Set the locale for formatting."""
    global _LOCALE
    _LOCALE = locale


def get_locale() -> str:
    """Get the current locale."""
    return _LOCALE


def set_formatter(formatter) -> None:
    """Set a custom formatter."""
    global _FORMATTER
    _FORMATTER = formatter


def get_formatter():
    """Get the current formatter."""
    return _FORMATTER


def week_starts_at(day: int) -> None:
    """Set the first day of the week."""
    global _WEEK_STARTS_AT
    _WEEK_STARTS_AT = day


def week_ends_at(day: int) -> None:
    """Set the last day of the week."""
    global _WEEK_ENDS_AT
    _WEEK_ENDS_AT = day


def TEST_MODE(value: bool = True) -> None:
    """Enable or disable test mode."""
    global _TEST_MODE
    _TEST_MODE = value


def datetime(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    microsecond: int = 0,
    tz: Optional[Union[str, Timezone]] = None,
) -> DateTime:
    """
    Create a new DateTime instance.
    
    Args:
        year: The year
        month: The month
        day: The day
        hour: The hour (0-23)
        minute: The minute (0-59)
        second: The second (0-59)
        microsecond: The microsecond (0-999999)
        tz: The timezone (string or Timezone object)
    
    Returns:
        A DateTime instance
    """
    return DateTime.create(
        year, month, day, hour, minute, second, microsecond, tz
    )


def parse(
    text: str,
    tz: Optional[Union[str, Timezone]] = None,
    strict: bool = True,
) -> DateTime:
    """
    Parse a string into a DateTime instance.
    
    Args:
        text: The string to parse
        tz: The timezone to use if not present in the string
        strict: Whether to use strict parsing
    
    Returns:
        A DateTime instance
    """
    from .parsing import parse as _parse
    return _parse(text, tz, strict)


def now(tz: Optional[Union[str, Timezone]] = None) -> DateTime:
    """
    Get a DateTime instance for the current moment.
    
    Args:
        tz: The timezone
    
    Returns:
        A DateTime instance
    """
    return DateTime.now(tz)


def today(tz: Optional[Union[str, Timezone]] = None) -> DateTime:
    """
    Create a DateTime instance for today.
    
    Args:
        tz: The timezone
    
    Returns:
        A DateTime instance
    """
    dt = now(tz)
    return datetime(dt.year, dt.month, dt.day, tz=dt.timezone)


def tomorrow(tz: Optional[Union[str, Timezone]] = None) -> DateTime:
    """
    Create a DateTime instance for tomorrow.
    
    Args:
        tz: The timezone
    
    Returns:
        A DateTime instance
    """
    return today(tz).add(days=1)


def yesterday(tz: Optional[Union[str, Timezone]] = None) -> DateTime:
    """
    Create a DateTime instance for yesterday.
    
    Args:
        tz: The timezone
    
    Returns:
        A DateTime instance
    """
    return today(tz).subtract(days=1)


def timezone(name: str) -> Timezone:
    """
    Create a Timezone instance from a timezone name.
    
    Args:
        name: The timezone name
    
    Returns:
        A Timezone instance
    """
    return Timezone(name)


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
    """
    Create a Duration instance.
    
    Args:
        years: Number of years
        months: Number of months
        weeks: Number of weeks
        days: Number of days
        hours: Number of hours
        minutes: Number of minutes
        seconds: Number of seconds
        microseconds: Number of microseconds
    
    Returns:
        A Duration instance
    """
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


def from_timestamp(
    timestamp: Union[int, float],
    tz: Optional[Union[str, Timezone]] = None,
) -> DateTime:
    """
    Create a DateTime instance from a timestamp.
    
    Args:
        timestamp: Unix timestamp
        tz: The timezone
    
    Returns:
        A DateTime instance
    """
    return DateTime.from_timestamp(timestamp, tz)


# Monkey-patch the datetime module for compatibility
sys.modules[__name__].__class__.datetime = staticmethod(datetime)