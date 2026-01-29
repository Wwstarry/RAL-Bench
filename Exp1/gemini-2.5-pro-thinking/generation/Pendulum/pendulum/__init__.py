# pendulum/__init__.py
"""
A pure Python datetime library for cleaner, easier datetime handling.
"""
from __future__ import annotations

from .datetime import DateTime
from .duration import Duration, duration
from .timezone import Timezone, timezone, UTC
from .formatting import parse

# Version
__version__ = "3.0.0"  # Mock version to be compatible with tests

# Constants
MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6

def datetime(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    microsecond: int = 0,
    tz: str | Timezone | None = "UTC",
) -> DateTime:
    """
    Creates a new DateTime instance.
    """
    if isinstance(tz, str):
        tz_info = timezone(tz)
    else:
        tz_info = tz

    return DateTime(year, month, day, hour, minute, second, microsecond, tzinfo=tz_info)


def now(tz: str | Timezone | None = None) -> DateTime:
    """
    Gets the current time as a DateTime instance.
    Defaults to UTC, unlike datetime.now().
    """
    if tz is None:
        tz = UTC
    return DateTime.now(tz)


def from_timestamp(timestamp: float, tz: str | Timezone = "UTC") -> DateTime:
    """
    Create a DateTime instance from a timestamp.
    """
    if isinstance(tz, str):
        tz = timezone(tz)

    dt = DateTime.fromtimestamp(timestamp, tz=tz)
    return dt

# Expose classes and functions
__all__ = [
    "DateTime",
    "Duration",
    "Timezone",
    "UTC",
    "datetime",
    "duration",
    "now",
    "parse",
    "timezone",
    "from_timestamp",
]