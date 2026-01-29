from __future__ import annotations

import datetime as _dt
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .i18n import ngettext


_UNIT_SECONDS: Dict[str, int] = {
    "seconds": 1,
    "minutes": 60,
    "hours": 60 * 60,
    "days": 60 * 60 * 24,
    "weeks": 60 * 60 * 24 * 7,
    "months": 60 * 60 * 24 * 30,   # 30 days approximation
    "years": 60 * 60 * 24 * 365,   # 365 days
}

_ORDER: List[str] = ["years", "months", "weeks", "days", "hours", "minutes", "seconds"]


def _to_seconds(value: Any) -> Decimal:
    if isinstance(value, _dt.timedelta):
        return Decimal(value.total_seconds())
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    raise TypeError("value must be a timedelta or a number of seconds")


def _plural(unit: str, n: int) -> str:
    singular = unit[:-1] if unit.endswith("s") else unit
    return ngettext(singular, unit, n)


def precisedelta(
    value: Any,
    minimum_unit: str = "seconds",
    format: str = "%d",
    suppress: Optional[Iterable[str]] = None,
    delimiter: str = ", ",
) -> str:
    if minimum_unit not in _UNIT_SECONDS:
        raise ValueError(f"unknown unit: {minimum_unit}")

    total = _to_seconds(value)
    sign = "-" if total < 0 else ""
    total = abs(total)

    suppress_set = set(suppress or ())
    # Unknown suppress entries are ignored.

    min_index = _ORDER.index(minimum_unit)

    # Truncate to minimum_unit (discard remainder below minimum_unit).
    min_sec = Decimal(_UNIT_SECONDS[minimum_unit])
    if min_sec != 0:
        total = (total // min_sec) * min_sec

    remaining = int(total)  # work in integer seconds after truncation
    parts: List[str] = []

    for unit in _ORDER[: min_index + 1]:
        if unit in suppress_set:
            continue
        unit_seconds = _UNIT_SECONDS[unit]
        count = remaining // unit_seconds
        remaining -= count * unit_seconds
        if count:
            num = format % count
            parts.append(f"{num} {_plural(unit, int(count))}")

    if not parts:
        # Nothing shown (e.g., everything suppressed or total is 0)
        count = 0
        num = format % count
        parts = [f"{num} {_plural(minimum_unit, count)}"]

    return sign + delimiter.join(parts)


def naturaldelta(value: Any, months: bool = True) -> str:
    seconds = _to_seconds(value)
    seconds = abs(seconds)
    s = float(seconds)

    if s < 1:
        return "a moment"
    if s < 45:
        return "a moment"
    if s < 90:
        return "a minute"

    minutes = s / 60.0
    if minutes < 45:
        n = int(round(minutes))
        return f"{n} minutes"
    if minutes < 90:
        return "an hour"

    hours = minutes / 60.0
    if hours < 22:
        n = int(round(hours))
        return f"{n} hours"
    if hours < 36:
        return "a day"

    days = hours / 24.0
    if days < 25:
        n = int(round(days))
        return f"{n} days"

    if months:
        if days < 45:
            return "a month"
        if days < 345:
            n = int(round(days / 30.0))
            n = max(2, n)
            return f"{n} months"
        if days < 545:
            return "a year"
        n = int(round(days / 365.0))
        return f"{n} years"
    else:
        # Weeks-based fallback if months=False
        weeks = days / 7.0
        if days < 45:
            n = int(round(weeks))
            n = max(5, n)
            return f"{n} weeks"
        if days < 365:
            n = int(round(weeks))
            return f"{n} weeks"
        if days < 545:
            return "a year"
        n = int(round(days / 365.0))
        return f"{n} years"


def naturaltime(value: Any, when: Optional[_dt.datetime] = None) -> str:
    # Determine delta seconds: positive -> future, negative -> past
    if isinstance(value, _dt.datetime):
        ref = when
        if ref is None:
            if value.tzinfo is not None:
                ref = _dt.datetime.now(tz=value.tzinfo)
            else:
                ref = _dt.datetime.now()
        delta = value - ref  # may raise TypeError for naive/aware mismatch
        seconds = Decimal(delta.total_seconds())
    elif isinstance(value, _dt.timedelta):
        seconds = Decimal(value.total_seconds())
    elif isinstance(value, (int, float, Decimal)):
        seconds = Decimal(str(value))
    else:
        raise TypeError("value must be datetime, timedelta, or seconds")

    s = float(seconds)

    if abs(s) < 1:
        return "now"

    phrase = naturaldelta(abs(seconds), months=True)

    if s < 0:
        # Past
        if phrase == "a moment":
            # Many implementations prefer "a moment ago" for short past deltas.
            return "a moment ago"
        return f"{phrase} ago"
    else:
        # Future
        if phrase == "a moment":
            return "in a moment"
        return f"in {phrase}"