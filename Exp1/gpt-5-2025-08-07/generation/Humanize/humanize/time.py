"""
Time and delta humanization helpers.
"""

from datetime import datetime, timedelta
from typing import Iterable, Tuple, Union, Optional, Dict

Number = Union[int, float]
TimeLike = Union[datetime, timedelta, Number]


def _total_seconds(td: timedelta) -> float:
    # Python 3's timedelta has total_seconds, but ensure consistent
    return td.total_seconds()


def _indefinite_article(word: str) -> str:
    # Basic indefinite article decision: 'an' for vowel starts and special-case 'hour' (silent h)
    w = word.lower()
    if w.startswith(("a", "e", "i", "o", "u")) or w.startswith("hour"):
        return "an"
    return "a"


def _fuzzy_components(seconds: float) -> Tuple[str, int]:
    """
    Convert number of seconds to a fuzzy unit and count following common thresholds.

    Returns (unit, count) where unit is one of:
    'moment', 'second', 'minute', 'hour', 'day', 'week', 'month', 'year'

    Logic inspired by common timeago thresholds.
    """
    s = abs(seconds)
    if s < 1:
        return ("moment", 0)
    if s < 45:
        return ("second", int(round(s)))
    if s < 90:
        return ("minute", 1)
    m = s / 60.0
    if m < 45:
        return ("minute", int(round(m)))
    if m < 90:
        return ("hour", 1)
    h = m / 60.0
    if h < 24:
        return ("hour", int(round(h)))
    if h < 42:
        return ("day", 1)
    d = h / 24.0
    if d < 30:
        return ("day", int(round(d)))
    if d < 45:
        return ("month", 1)
    mo = d / 30.0
    if mo < 12:
        return ("month", int(round(mo)))
    if mo < 18:
        return ("year", 1)
    y = mo / 12.0
    return ("year", int(round(y)))


def _pluralize(unit: str, count: int) -> str:
    if unit == "moment":
        return "moment"
    if count == 1:
        return unit
    return unit + "s"


def naturaldelta(value: TimeLike) -> str:
    """
    Human-readable, fuzzy, directionless delta string.

    Accepts a timedelta, a datetime (compared to now), or a number of seconds.
    """
    seconds = 0.0
    if isinstance(value, datetime):
        seconds = abs(_total_seconds(datetime.now(value.tzinfo) - value))
    elif isinstance(value, timedelta):
        seconds = abs(_total_seconds(value))
    else:
        try:
            seconds = abs(float(value))
        except Exception:
            return str(value)

    unit, count = _fuzzy_components(seconds)
    if unit == "moment":
        return "a moment"
    if count == 1:
        art = _indefinite_article(unit)
        return f"{art} {unit}"
    else:
        return f"{count} {_pluralize(unit, count)}"


def naturaltime(value: TimeLike, when: Optional[datetime] = None) -> str:
    """
    Human-readable, fuzzy time relative to now.

    - If value is a datetime, computes the delta to 'when' (default now).
    - If value is a timedelta or number, treats positive values as in the future
      and negative values as in the past.
    """
    now = when or datetime.now(getattr(value, "tzinfo", None) if isinstance(value, datetime) else None)

    if isinstance(value, datetime):
        delta = now - value
        seconds = _total_seconds(delta)
        if abs(seconds) < 1:
            return "now"
        phrase = naturaldelta(delta)
        return f"{phrase} ago" if seconds > 0 else f"in {phrase}"
    elif isinstance(value, timedelta):
        seconds = _total_seconds(value)
    else:
        try:
            seconds = float(value)
        except Exception:
            return str(value)

    if abs(seconds) < 1:
        return "now"
    phrase = naturaldelta(seconds)
    return f"in {phrase}" if seconds > 0 else f"{phrase} ago"


def _get_seconds(value: Union[timedelta, Number, datetime], end: Optional[datetime] = None) -> float:
    """
    Compute total seconds for value, optionally using end if value is a datetime.
    """
    if isinstance(value, datetime):
        ref = end or datetime.now(value.tzinfo)
        return _total_seconds(value - ref)
    elif isinstance(value, timedelta):
        return _total_seconds(value)
    else:
        return float(value)


def _unit_table() -> Dict[str, float]:
    # Define units in seconds
    return {
        "years": 365.0 * 24 * 3600,
        "months": 30.0 * 24 * 3600,
        "weeks": 7.0 * 24 * 3600,
        "days": 24.0 * 3600,
        "hours": 3600.0,
        "minutes": 60.0,
        "seconds": 1.0,
        "milliseconds": 1e-3,
        "microseconds": 1e-6,
    }


def _singular(unit: str) -> str:
    if unit.endswith("s"):
        return unit[:-1]
    return unit


def _format_list(parts: Iterable[str]) -> str:
    items = list(parts)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + " and " + items[-1]


def precisedelta(
    delta: Union[timedelta, Number, datetime],
    minimum_unit: str = "seconds",
    suppress: Iterable[str] = (),
    format: str = "%.0f",
    **kwargs,
) -> str:
    """
    Create a precise, directionless description of the time delta.

    - delta: timedelta or number of seconds; if datetime, difference is computed to now
    - minimum_unit: the smallest unit to include. One of:
      'years','months','weeks','days','hours','minutes','seconds','milliseconds','microseconds'
      If minimum_unit is larger than 'seconds', the remainder is expressed as a fraction
      of the minimum unit using the provided format string.
    - suppress: iterable of unit names to skip entirely.
    - format: format string applied to the smallest unit when producing a fractional value
      or when minimum_unit is reached and fractional representation is desired.

    The output uses pluralization ("1 hour", "2 hours") and Oxford-comma style.
    """
    units_in_seconds = _unit_table()

    if minimum_unit not in units_in_seconds:
        # Fallback to seconds if unknown
        minimum_unit = "seconds"
    suppress = set(suppress or ())

    total_seconds = _get_seconds(delta)
    seconds_abs = abs(total_seconds)

    # Build ordered units from largest to smallest until minimum_unit
    order = ["years", "months", "weeks", "days", "hours", "minutes", "seconds", "milliseconds", "microseconds"]
    # Limit order down to minimum unit
    end_index = order.index(minimum_unit)
    consider = order[: end_index + 1]

    remaining = seconds_abs
    parts = []

    # Consume all units above the minimum
    for unit in consider[:-1]:
        if unit in suppress:
            continue
        unit_seconds = units_in_seconds[unit]
        count = int(remaining // unit_seconds)
        if count > 0:
            parts.append(f"{count} {_singular(unit) if count == 1 else unit}")
            remaining -= count * unit_seconds

    # Minimum unit handling
    min_unit = consider[-1]
    if min_unit not in suppress:
        min_seconds = units_in_seconds[min_unit]
        # If the minimum unit is seconds or lower, show integer counts
        if min_unit in ("seconds", "milliseconds", "microseconds"):
            count = int(round(remaining / min_seconds))
            # Edge case: rounding may push to next unit when count == base (e.g., 1000 ms)
            # We'll simply display as is in the min unit
            if count > 0 or not parts:
                parts.append(f"{count} {_singular(min_unit) if count == 1 else min_unit}")
        else:
            # Express remainder as fractional of the min unit using provided format
            value = remaining / min_seconds
            # If we have no larger parts and nothing remains (value ~ 0), ensure we display 0 of the min unit
            if value == 0 and not parts:
                parts.append(f"0 {min_unit}")
            elif value > 0 or not parts:
                out = format % value
                # pluralization based on value ~= 1
                try:
                    # If format yields something like '1.0', treat as singular
                    numeric = float(out)
                    unit_name = _singular(min_unit) if abs(numeric - 1.0) < 1e-12 else min_unit
                except Exception:
                    unit_name = min_unit
                parts.append(f"{out} {unit_name}")

    return _format_list(parts)