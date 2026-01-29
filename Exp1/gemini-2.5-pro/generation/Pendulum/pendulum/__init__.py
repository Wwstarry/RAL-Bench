# -*- coding: utf-8 -*-

"""
A pure Python implementation of the core Pendulum API.
"""

import datetime as _dt
from .datetime import DateTime
from .duration import Duration
from .timezone import Timezone, UTC, local_timezone
from .formatting import Formatter

# Constants
MONDAY = 1
TUESDAY = 2
WEDNESDAY = 3
THURSDAY = 4
FRIDAY = 5
SATURDAY = 6
SUNDAY = 7

# Public API
__all__ = [
    "DateTime",
    "Duration",
    "Timezone",
    "UTC",
    "now",
    "utcnow",
    "today",
    "tomorrow",
    "yesterday",
    "datetime",
    "duration",
    "from_timestamp",
    "local_timezone",
    "parse",
    "timezone",
]

_formatter = Formatter()

def datetime(
    year,
    month,
    day,
    hour=0,
    minute=0,
    second=0,
    microsecond=0,
    tz="UTC",
    fold=None,
):
    """
    Creates a new DateTime instance.
    """
    if fold is None:
        return DateTime(year, month, day, hour, minute, second, microsecond, tz=tz)
    
    return DateTime(year, month, day, hour, minute, second, microsecond, tz=tz, fold=fold)


def now(tz=None):
    """
    Get a DateTime instance for the current date and time.
    """
    if tz is None:
        tz = local_timezone()
    
    return DateTime.now(tz)


def utcnow():
    """
    Get a DateTime instance for the current date and time in UTC.
    """
    return DateTime.now(UTC)


def today(tz=None):
    """
    Get a DateTime instance for the current date.
    """
    return now(tz).start_of("day")


def tomorrow(tz=None):
    """
    Get a DateTime instance for tomorrow.
    """
    return today(tz).add(days=1)


def yesterday(tz=None):
    """
    Get a DateTime instance for yesterday.
    """
    return today(tz).subtract(days=1)


def from_timestamp(timestamp, tz="UTC"):
    """

    Create a DateTime instance from a timestamp.
    """
    return DateTime.fromtimestamp(timestamp, tz=tz)


def duration(**kwargs):
    """
    Creates a new Duration instance.
    """
    return Duration(**kwargs)


def timezone(tz):
    """
    Creates a new Timezone instance.
    """
    return Timezone(tz)


def parse(text, **options):
    """
    Parses a string representation of a date and time.
    """
    return DateTime.parse(text, **options)