from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Sequence, Tuple, Union

from .i18n import gettext, ngettext


@dataclass(frozen=True)
class _Unit:
    name_singular: str
    name_plural: str
    seconds: float


_UNITS: Tuple[_Unit, ...] = (
    _Unit(gettext("year"), gettext("years"), 365 * 24 * 3600),
    _Unit(gettext("month"), gettext("months"), 30 * 24 * 3600),
    _Unit(gettext("week"), gettext("weeks"), 7 * 24 * 3600),
    _Unit(gettext("day"), gettext("days"), 24 * 3600),
    _Unit(gettext("hour"), gettext("hours"), 3600),
    _Unit(gettext("minute"), gettext("minutes"), 60),
    _Unit(gettext("second"), gettext("seconds"), 1),
)


def _to_datetime(value: Any) -> _dt.datetime:
    if isinstance(value, _dt.datetime):
        return value
    if isinstance(value, _dt.date):
        return _dt.datetime(value.year, value.month, value.day)
    raise TypeError("Expected date or datetime")


def _to_timedelta(delta: Any) -> _dt.timedelta:
    if isinstance(delta, _dt.timedelta):
        return delta
    if isinstance(delta, (int, float)):
        return _dt.timedelta(seconds=float(delta))
    raise TypeError("Expected timedelta or seconds")


def _format_unit(count: int, singular: str, plural: str) -> str:
    word = ngettext(singular, plural, count)
    return f"{count} {word}"


def precisedelta(
    value: Any,
    minimum_unit: str = "seconds",
    format: str = "%0.0f",
    suppress: Sequence[str] = (),
) -> str:
    """
    Return a precise, human-readable breakdown of a timedelta.

    This is a pragmatic subset of the reference behavior. Supports:
    - value: timedelta or seconds
    - minimum_unit: one of: 'seconds','minutes','hours','days','weeks','months','years'
    - suppress: iterable of unit names to omit (plural form names acceptable)
    - format: applied to counts for the smallest unit (approximate compatibility)
    """
    delta = _to_timedelta(value)
    total_seconds = delta.total_seconds()
    if total_seconds == 0:
        return _format_unit(0, gettext("second"), gettext("seconds"))

    sign = "-" if total_seconds < 0 else ""
    remaining = abs(total_seconds)

    min_unit = minimum_unit.lower()
    unit_names = [u.name_plural for u in _UNITS]
    # Accept singular/plural
    min_seconds = 1
    for u in _UNITS:
        if min_unit in (u.name_singular.lower(), u.name_plural.lower()):
            min_seconds = u.seconds
            break

    suppress_set = {s.lower() for s in suppress}

    parts: List[str] = []
    for u in _UNITS:
        # stop when reaching minimum unit
        if u.seconds < min_seconds:
            continue
        if u.name_singular.lower() in suppress_set or u.name_plural.lower() in suppress_set:
            continue
        if u.seconds == min_seconds:
            # smallest considered unit: round to nearest integer count
            count = int(round(remaining / u.seconds))
            if count or parts:
                parts.append(_format_unit(count, u.name_singular, u.name_plural))
            remaining = 0
            break
        count = int(remaining // u.seconds)
        if count:
            parts.append(_format_unit(count, u.name_singular, u.name_plural))
            remaining -= count * u.seconds

    if not parts:
        parts = [_format_unit(0, gettext("second"), gettext("seconds"))]
    return sign + ", ".join(parts)


def naturaldelta(value: Any) -> str:
    """
    Humanize a timedelta or seconds (duration) without direction.
    """
    delta = _to_timedelta(value)
    seconds = abs(int(round(delta.total_seconds())))
    if seconds <= 1:
        return _format_unit(seconds, gettext("second"), gettext("seconds"))

    for u in _UNITS:
        if seconds >= u.seconds:
            count = int(round(seconds / u.seconds))
            if count == 0:
                count = 1
            return _format_unit(count, u.name_singular, u.name_plural)
    return _format_unit(seconds, gettext("second"), gettext("seconds"))


def naturaltime(value: Any, when: Optional[_dt.datetime] = None) -> str:
    """
    Humanize a datetime/date relative to `when` (default: now, local time).

    Examples:
      - "a moment ago"
      - "3 minutes ago"
      - "in 2 hours"
    """
    if when is None:
        when = _dt.datetime.now(tz=value.tzinfo) if isinstance(value, _dt.datetime) and value.tzinfo else _dt.datetime.now()

    dt = _to_datetime(value)
    # Normalize naive/aware mismatch by dropping tzinfo if needed
    if (dt.tzinfo is None) != (when.tzinfo is None):
        dt = dt.replace(tzinfo=None)
        when = when.replace(tzinfo=None)

    delta = dt - when
    seconds = delta.total_seconds()
    future = seconds > 0
    seconds = abs(seconds)

    if seconds < 10:
        s = gettext("a moment")
    elif seconds < 60:
        s = _format_unit(int(round(seconds)), gettext("second"), gettext("seconds"))
    elif seconds < 3600:
        s = _format_unit(int(round(seconds / 60)), gettext("minute"), gettext("minutes"))
    elif seconds < 86400:
        s = _format_unit(int(round(seconds / 3600)), gettext("hour"), gettext("hours"))
    elif seconds < 86400 * 7:
        s = _format_unit(int(round(seconds / 86400)), gettext("day"), gettext("days"))
    elif seconds < 86400 * 30:
        s = _format_unit(int(round(seconds / (86400 * 7))), gettext("week"), gettext("weeks"))
    elif seconds < 86400 * 365:
        s = _format_unit(int(round(seconds / (86400 * 30))), gettext("month"), gettext("months"))
    else:
        s = _format_unit(int(round(seconds / (86400 * 365))), gettext("year"), gettext("years"))

    if s == gettext("a moment"):
        return gettext("in a moment") if future else gettext("a moment ago")
    return (gettext("in %s") % s) if future else (gettext("%s ago") % s)