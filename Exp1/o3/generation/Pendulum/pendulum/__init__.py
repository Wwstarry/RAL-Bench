"""
A **very** small subset of the real ``pendulum`` API.

This implementation is *not* a full-featured drop-in replacement for the
awesome ``pendulum`` project – it only exposes just enough behaviour for a set
of educational/assessment tests that rely on a handful of public helpers.

Only pure-python standard-library modules are used, no external dependency is
required.
"""
from __future__ import annotations

from datetime import datetime as _datetime, timedelta as _timedelta, timezone as _tz

from .datetime import DateTime
from .duration import Duration
from .timezone import timezone as _timezone, UTC
from .utils import _make_datetime_kwargs

# ---------------------------------------------------------------------------
# Public helpers – keep the signatures identical to real pendulum where
# possible.  The heavy lifting is delegated to the internal modules.
# ---------------------------------------------------------------------------

def datetime(  # noqa: D401  (keep the name consistent with real pendulum)
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    microsecond: int = 0,
    tz: str | int | float | None = None,
):
    """
    Build a timezone aware pendulum ``DateTime``.

    If *tz* is:
      * ``None``         – the resulting instance is naïve (i.e. ``tzinfo`` is
                           ``None``)
      * str              – resolved via :pyfunc:`pendulum.timezone`
      * int|float        – interpreted as *fixed* offset in **seconds**
    """
    kw = _make_datetime_kwargs(
        year,
        month,
        day,
        hour,
        minute,
        second,
        microsecond,
        tz,
    )
    return DateTime(**kw)


def parse(timestring: str, tz: str | int | float | None = None) -> DateTime:
    """
    Parse a (reasonably simple) ISO-8601 formatted string.
    """
    from .datetime import _parse_iso_datetime  # local import to avoid cycles

    dt = _parse_iso_datetime(timestring)
    if tz is not None:
        dt = dt.in_timezone(tz)
    return dt


def timezone(tz: str | int | float | None = None):
    """
    Resolve *tz* to a proper ``tzinfo`` instance.

    If *tz* is:
      * ``None`` – ``UTC`` is returned
      * str      – resolved from the IANA db via ``zoneinfo.ZoneInfo``
      * int/float - treated as fixed offset in **seconds**
    """
    return _timezone(tz)


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
    Build a small *duration* object.
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


# Public re-exports to have the same look-and-feel as the original project.
__all__ = [
    "UTC",
    "DateTime",
    "Duration",
    "datetime",
    "parse",
    "timezone",
    "duration",
]