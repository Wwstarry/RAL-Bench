from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Set

from .i18n import ngettext, gettext


_UNIT_SECONDS: Dict[str, int] = {
    "years": 365 * 24 * 3600,
    "months": 30 * 24 * 3600,
    "days": 24 * 3600,
    "hours": 3600,
    "minutes": 60,
    "seconds": 1,
}


def _to_seconds(value: Any, *, when: Optional[_dt.datetime] = None) -> float:
    if isinstance(value, _dt.timedelta):
        return value.total_seconds()

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, _dt.date) and not isinstance(value, _dt.datetime):
        value = _dt.datetime.combine(value, _dt.time.min)

    if isinstance(value, _dt.datetime):
        ref = when or _dt.datetime.now(tz=value.tzinfo) if value.tzinfo else (when or _dt.datetime.now())
        if isinstance(ref, _dt.date) and not isinstance(ref, _dt.datetime):
            ref = _dt.datetime.combine(ref, _dt.time.min)

        # Handle naive/aware mismatch gracefully.
        try:
            delta = value - ref
        except TypeError:
            v2 = value.replace(tzinfo=None)
            r2 = ref.replace(tzinfo=None) if isinstance(ref, _dt.datetime) else ref
            delta = v2 - r2
        return delta.total_seconds()

    raise ValueError("unsupported type for time delta")


def _units(months: bool) -> List[Tuple[str, int]]:
    if months:
        order = ["years", "months", "days", "hours", "minutes", "seconds"]
    else:
        order = ["years", "days", "hours", "minutes", "seconds"]
    return [(name, _UNIT_SECONDS[name]) for name in order]


def naturaldelta(value: Any, months: bool = False, minimum_unit: str = "seconds") -> str:
    seconds = abs(_to_seconds(value))
    unit_list = _units(months)

    if minimum_unit not in _UNIT_SECONDS:
        raise ValueError("invalid minimum_unit")

    min_seconds = _UNIT_SECONDS[minimum_unit]

    if seconds == 0:
        # reference humanize often returns "0 seconds" for naturaldelta
        return _format_unit(0, minimum_unit)

    # Ensure we never go below minimum_unit; if below, return "1 <min_unit>"
    if seconds < min_seconds:
        return _format_unit(1, minimum_unit)

    for name, unit_seconds in unit_list:
        if unit_seconds < min_seconds:
            continue
        count = int(seconds // unit_seconds)
        if count:
            return _format_unit(count, name)

    # Fallback (shouldn't happen)
    return _format_unit(1, minimum_unit)


def naturaltime(
    value: Any,
    future: bool = False,
    months: bool = False,
    minimum_unit: str = "seconds",
    when: Optional[_dt.datetime] = None,
) -> str:
    seconds = _to_seconds(value, when=when)

    # In humanize, negative timedelta typically means "ago" when passed as a datetime diff.
    # We interpret: seconds < 0 => value is in the past relative to `when`.
    if seconds == 0:
        return gettext("now")

    if abs(seconds) < 10:
        if seconds < 0 and not future:
            return gettext("a moment ago")
        if seconds < 0 and future:
            return gettext("in a moment")
        if seconds > 0 and future:
            return gettext("in a moment")
        return gettext("a moment ago")

    if seconds < 0 and not future:
        phrase = naturaldelta(-seconds, months=months, minimum_unit=minimum_unit)
        return gettext("%(delta)s ago") % {"delta": phrase}
    else:
        phrase = naturaldelta(abs(seconds), months=months, minimum_unit=minimum_unit)
        return gettext("in %(delta)s") % {"delta": phrase}


def precisedelta(
    value: Any,
    minimum_unit: str = "seconds",
    format: str = "%0.1f",
    suppress: Optional[Iterable[str]] = None,
    months: bool = False,
) -> str:
    total = abs(_to_seconds(value))

    if minimum_unit not in _UNIT_SECONDS:
        raise ValueError("invalid minimum_unit")

    min_seconds = _UNIT_SECONDS[minimum_unit]
    unit_list = _units(months)

    suppress_set: Set[str] = set(suppress or [])
    parts: List[str] = []

    if total == 0:
        return _format_unit(0, minimum_unit)

    # If below minimum, return 1 minimum unit.
    if total < min_seconds:
        return _format_unit(1, minimum_unit)

    remaining = int(total)

    for name, unit_seconds in unit_list:
        if name in suppress_set:
            continue
        if unit_seconds < min_seconds:
            continue
        count = remaining // unit_seconds
        if count:
            remaining -= count * unit_seconds
            parts.append(_format_unit(int(count), name))

    if not parts:
        return _format_unit(1, minimum_unit)

    return ", ".join(parts)


def _format_unit(count: int, unit_plural: str) -> str:
    singular = unit_plural[:-1] if unit_plural.endswith("s") else unit_plural
    label = ngettext(singular, unit_plural, count)
    return f"{count} {label}"