"""
Human-friendly time & delta helpers – a compact subset of the reference API.
"""

from __future__ import annotations

import datetime as _dt
from typing import Any, Tuple


# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def _to_timedelta(value: Any) -> _dt.timedelta:
    """
    Convert an arbitrary object to ``datetime.timedelta`` for internal use.
    Accepts:

    * ``datetime.timedelta`` – returned unchanged.
    * ``int`` / ``float`` – treated as *seconds*.
    """
    if isinstance(value, _dt.timedelta):
        return value
    if isinstance(value, (int, float)):
        return _dt.timedelta(seconds=float(value))
    raise TypeError(
        f"{value!r} is not a timedelta or a number of seconds"
    )


def _split_timedelta(delta: _dt.timedelta) -> Tuple[int, int, int, int, int, int]:
    """
    Break *delta* into (years, months, days, hours, minutes, seconds).
    Months are assumed to be 30 days, years 365 days – matching the
    approximation used by the reference implementation.
    """
    total_seconds = int(abs(delta.total_seconds()))
    sign = -1 if delta.total_seconds() < 0 else 1

    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    years, days = divmod(days, 365)
    months, days = divmod(days, 30)

    return sign, years, months, days, hours, minutes, seconds


# --------------------------------------------------------------------------- #
# Public helpers
# --------------------------------------------------------------------------- #
def precisedelta(
    value: Any,
    *,
    minimum_unit: str | None = None,
) -> str:
    """
    Detailed / *precise* rendering of time deltas, e.g. “1 day 2 hours
    3 minutes”.

    Only years, months, days, hours, minutes and seconds are produced.
    """
    delta = _to_timedelta(value)
    sign, years, months, days, hours, minutes, seconds = _split_timedelta(delta)

    units = [
        (years, "year"),
        (months, "month"),
        (days, "day"),
        (hours, "hour"),
        (minutes, "minute"),
        (seconds, "second"),
    ]

    pieces = []
    passed_min_unit = minimum_unit is None
    for amount, name in units:
        if amount:
            passed_min_unit = True
        if not passed_min_unit:
            # ignore until we reach *minimum_unit*
            if name == minimum_unit:
                passed_min_unit = True
            else:
                continue

        if passed_min_unit:
            if amount:
                plural = "" if amount == 1 else "s"
                pieces.append(f"{amount} {name}{plural}")

    if not pieces:
        # All components were zero
        pieces.append(f"0 {minimum_unit or 'seconds'}")

    result = " ".join(pieces)
    if sign < 0:
        result = "-" + result
    return result


def naturaldelta(value: Any) -> str:
    """
    Produces an *approximate* human readable difference such as “a minute”
    or “3 weeks”.
    """
    delta = _to_timedelta(value)
    seconds = abs(int(delta.total_seconds()))

    if seconds < 45:
        return "a few seconds"
    if seconds < 90:
        return "a minute"
    minutes = seconds / 60
    if minutes < 45:
        return f"{round(minutes):.0f} minutes"
    if minutes < 90:
        return "an hour"
    hours = minutes / 60
    if hours < 22:
        return f"{round(hours):.0f} hours"
    if hours < 36:
        return "a day"
    days = hours / 24
    if days < 25:
        return f"{round(days):.0f} days"
    if days < 45:
        return "a month"
    if days < 345:
        return f"{round(days / 30):.0f} months"
    if days < 545:
        return "a year"
    return f"{round(days / 365):.0f} years"


def naturaltime(timestamp: Any, *, when: _dt.datetime | None = None) -> str:
    """
    Natural rendering of a point in time relative to *when* (defaults to *now*).
    """
    if when is None:
        when = _dt.datetime.now(tz=getattr(timestamp, "tzinfo", None))
    if isinstance(timestamp, _dt.timedelta):
        # If a timedelta is handed in, treat as "when + delta"
        timestamp = when + timestamp
    if not isinstance(timestamp, _dt.datetime):
        # Accept seconds as offset from *when*
        timestamp = when + _dt.timedelta(seconds=float(timestamp))
    delta = when - timestamp

    if abs(delta.total_seconds()) < 1:
        return "now"

    description = naturaldelta(delta)
    if delta.total_seconds() > 0:
        return f"{description} ago"
    return f"in {description}"