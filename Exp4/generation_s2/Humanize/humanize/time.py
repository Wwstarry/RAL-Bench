from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, Iterable, Optional, Tuple, Union

TimeLike = Union[int, float, _dt.timedelta]


_UNITS: Tuple[Tuple[str, int], ...] = (
    ("year", 365 * 24 * 60 * 60),
    ("month", 30 * 24 * 60 * 60),
    ("day", 24 * 60 * 60),
    ("hour", 60 * 60),
    ("minute", 60),
    ("second", 1),
)


def _as_timedelta(value: Any) -> Optional[_dt.timedelta]:
    if value is None:
        return None
    if isinstance(value, _dt.timedelta):
        return value
    if isinstance(value, (int, float)):
        return _dt.timedelta(seconds=float(value))
    return None


def _plural(n: int, word: str) -> str:
    return word if n == 1 else word + "s"


def precisedelta(
    value: Any,
    minimum_unit: str = "seconds",
    format: str = "%0.0f",
    suppress: Iterable[str] = (),
    locale: str | None = None,  # compatibility
) -> str:
    """
    Render a timedelta into a precise, multi-unit string.

    This is a pragmatic subset compatible with common expectations of humanize:
    - breaks down into years/months/days/hours/minutes/seconds
    - supports suppressing units (e.g. ('seconds',))
    - minimum_unit controls the smallest unit included
    """
    td = _as_timedelta(value)
    if td is None:
        return str(value)

    total_seconds = int(round(abs(td.total_seconds())))
    if total_seconds == 0:
        return "0 seconds"

    suppress_set = {s.rstrip("s") for s in suppress}
    min_unit = minimum_unit.rstrip("s")

    # Determine where to stop
    unit_names = [u for (u, _) in _UNITS]
    if min_unit not in unit_names:
        min_unit = "second"
    stop_index = unit_names.index(min_unit)

    parts = []
    remaining = total_seconds
    for idx, (name, seconds_per) in enumerate(_UNITS):
        if idx < stop_index:
            # bigger units
            count = remaining // seconds_per
            remaining = remaining % seconds_per
        elif idx == stop_index:
            count = remaining // seconds_per
            remaining = remaining % seconds_per
        else:
            # smaller than minimum_unit: ignore
            count = 0

        if name in suppress_set:
            continue
        if idx > stop_index:
            continue
        if count:
            parts.append(f"{count} {_plural(int(count), name)}")

    if not parts:
        # everything suppressed; fall back to minimum unit
        return f"0 {_plural(0, min_unit)}"

    # restore sign by prefixing '-' (reference often doesn't include sign here, but safe)
    if td.total_seconds() < 0:
        return "-" + ", ".join(parts)
    return ", ".join(parts)


def naturaldelta(
    value: Any,
    months: bool = True,
    minimum_unit: str = "seconds",
    locale: str | None = None,
) -> str:
    """
    Like precisedelta but more compact (single largest unit), e.g. "3 days".
    """
    td = _as_timedelta(value)
    if td is None:
        return str(value)

    seconds = abs(td.total_seconds())
    if seconds < 1:
        return "a moment"

    # Pick units; optionally remove months/years approximations.
    units = list(_UNITS)
    if not months:
        units = [u for u in units if u[0] not in ("month", "year")]

    min_unit = minimum_unit.rstrip("s")
    names = [u for (u, _) in units]
    if min_unit not in names:
        min_unit = "second"
    # don't return smaller than minimum unit
    min_idx = names.index(min_unit)

    for idx, (name, secs) in enumerate(units):
        if idx < min_idx:
            continue
        count = int(seconds // secs)
        if count >= 1:
            return f"{count} {_plural(count, name)}"

    # If none matched above min unit (e.g. seconds < 60 and min_unit=minute)
    return f"0 {_plural(0, min_unit)}"


def naturaltime(
    value: Any,
    when: Optional[_dt.datetime] = None,
    locale: str | None = None,
) -> str:
    """
    Convert a datetime/timedelta/seconds offset into a human readable relative string.

    Examples:
    - timedelta(seconds=3) -> "3 seconds ago"
    - timedelta(seconds=-3) -> "3 seconds from now"
    - datetime in past -> "... ago"
    """
    now = when or _dt.datetime.now(_dt.timezone.utc).astimezone().replace(tzinfo=None)

    if isinstance(value, _dt.datetime):
        dt = value
        if dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        delta = dt - now
    elif isinstance(value, _dt.date) and not isinstance(value, _dt.datetime):
        dt = _dt.datetime.combine(value, _dt.time.min)
        delta = dt - now
    else:
        td = _as_timedelta(value)
        if td is None:
            # maybe seconds in a string
            try:
                td = _dt.timedelta(seconds=float(value))
            except Exception:
                return str(value)
        delta = td

    seconds = delta.total_seconds()
    if abs(seconds) < 1:
        return "now"

    tense = "from now" if seconds > 0 else "ago"
    human = naturaldelta(_dt.timedelta(seconds=abs(seconds)))
    return f"{human} {tense}"