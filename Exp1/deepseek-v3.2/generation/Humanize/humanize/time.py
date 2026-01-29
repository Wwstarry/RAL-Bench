"""
Time humanization utilities.
"""

import datetime
import time
from typing import Union, Optional

from humanize.i18n import gettext as _, ngettext

def _now() -> datetime.datetime:
    """Get current time, can be mocked for testing."""
    return datetime.datetime.now()

def _abs_timedelta(delta: datetime.timedelta) -> datetime.timedelta:
    """Return absolute timedelta."""
    if delta.days < 0:
        return -delta
    return delta

def naturaldelta(
    value: Union[datetime.timedelta, int, float],
    months: bool = True,
    minimum_unit: str = "seconds",
) -> str:
    """
    Return a natural representation of a timedelta or number of seconds.

    Args:
        value: Timedelta or seconds.
        months: If True, use months and years.
        minimum_unit: Smallest unit to display.

    Returns:
        Human-readable time delta.
    """
    if isinstance(value, (int, float)):
        value = datetime.timedelta(seconds=value)

    if not isinstance(value, datetime.timedelta):
        return str(value)

    delta = _abs_timedelta(value)
    seconds = int(delta.total_seconds())

    if seconds == 0:
        return _("a moment")

    # Years and months
    if months:
        years = seconds // (365 * 24 * 3600)
        if years > 0:
            return ngettext("%d year", "%d years", years) % years

        months = seconds // (30 * 24 * 3600)
        if months > 0:
            return ngettext("%d month", "%d months", months) % months

    # Weeks
    weeks = seconds // (7 * 24 * 3600)
    if weeks > 0:
        return ngettext("%d week", "%d weeks", weeks) % weeks

    # Days
    days = seconds // (24 * 3600)
    if days > 0:
        return ngettext("%d day", "%d days", days) % days

    # Hours
    hours = seconds // 3600
    if hours > 0:
        return ngettext("%d hour", "%d hours", hours) % hours

    # Minutes
    minutes = seconds // 60
    if minutes > 0:
        return ngettext("%d minute", "%d minutes", minutes) % minutes

    # Seconds
    if minimum_unit == "seconds":
        return ngettext("%d second", "%d seconds", seconds) % seconds
    else:
        return _("a moment")

def naturaltime(
    value: Union[datetime.datetime, datetime.date, int, float],
    future: bool = False,
    months: bool = True,
    minimum_unit: str = "seconds",
) -> str:
    """
    Return a natural representation of a time in the past or future.

    Args:
        value: Time to represent.
        future: If True, always use future tense.
        months: If True, use months and years.
        minimum_unit: Smallest unit to display.

    Returns:
        Human-readable time.
    """
    if isinstance(value, (int, float)):
        value = datetime.datetime.fromtimestamp(value)

    if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        value = datetime.datetime.combine(value, datetime.time.min)

    if not isinstance(value, datetime.datetime):
        return str(value)

    now = _now()
    if value > now:
        delta = value - now
        suffix = _("from now")
    else:
        delta = now - value
        suffix = _("ago")

    delta_str = naturaldelta(delta, months=months, minimum_unit=minimum_unit)

    if delta_str == _("a moment"):
        return delta_str

    return _("%s %s") % (delta_str, suffix)

def precisedelta(
    delta: Union[datetime.timedelta, int, float],
    format: str = "%0.2f",
    threshold: float = 0.85,
    minimum_unit: str = "seconds",
    suppress: tuple = ("seconds",),
) -> str:
    """
    Return a precise representation of a timedelta.

    Args:
        delta: Timedelta or seconds.
        format: Format string for numbers.
        threshold: When to switch to next unit.
        minimum_unit: Smallest unit to display.
        suppress: Units to suppress.

    Returns:
        Precise time delta.
    """
    if isinstance(delta, (int, float)):
        delta = datetime.timedelta(seconds=delta)

    if not isinstance(delta, datetime.timedelta):
        return str(delta)

    delta = _abs_timedelta(delta)
    seconds = delta.total_seconds()

    # Define units
    units = [
        ("years", 365 * 24 * 3600),
        ("months", 30 * 24 * 3600),
        ("weeks", 7 * 24 * 3600),
        ("days", 24 * 3600),
        ("hours", 3600),
        ("minutes", 60),
        ("seconds", 1),
    ]

    # Find starting unit
    start_idx = 0
    for i, (unit_name, unit_seconds) in enumerate(units):
        if unit_name == minimum_unit:
            start_idx = i
            break

    # Build result
    result_parts = []
    remaining = seconds

    for i in range(start_idx, len(units)):
        unit_name, unit_seconds = units[i]

        if unit_name in suppress:
            continue

        if remaining >= unit_seconds * threshold or i == len(units) - 1:
            value = remaining / unit_seconds
            if unit_name == "seconds" and value < 1:
                # For sub-second precision
                value_str = format % value
            else:
                value_str = format % value
                # Remove trailing zeros
                if "." in value_str:
                    value_str = value_str.rstrip("0").rstrip(".")

            result_parts.append(
                ngettext(f"{value_str} {unit_name[:-1]}", f"{value_str} {unit_name}", int(float(value_str)))
            )
            break

    if not result_parts:
        return _("0 seconds")

    return " ".join(result_parts)

def naturalday(value: Union[datetime.date, datetime.datetime], format: str = "%b %d") -> str:
    """
    Return a natural day representation.

    Args:
        value: Date to represent.
        format: Format string for non-special days.

    Returns:
        Human-readable day.
    """
    if isinstance(value, datetime.datetime):
        value = value.date()

    if not isinstance(value, datetime.date):
        return str(value)

    today = _now().date()
    if value == today:
        return _("today")
    elif value == today - datetime.timedelta(days=1):
        return _("yesterday")
    elif value == today + datetime.timedelta(days=1):
        return _("tomorrow")
    else:
        return value.strftime(format)

def naturaldate(value: Union[datetime.date, datetime.datetime]) -> str:
    """
    Return a natural date representation.

    Args:
        value: Date to represent.

    Returns:
        Human-readable date.
    """
    return naturalday(value)