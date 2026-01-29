from __future__ import annotations

import datetime as _dt
import re
from typing import Any, Dict, Optional, Tuple

_ISO_RE = re.compile(
    r"""
    ^
    (?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})
    (?:
        [T\s]
        (?P<hour>\d{2})
        (?:
            :(?P<minute>\d{2})
        )?
        (?:
            :(?P<second>\d{2})
        )?
        (?:
            \.(?P<fraction>\d{1,6})
        )?
        (?:
            (?P<tz>Z|[+-]\d{2}(?::?\d{2})?)
        )?
    )?
    $
    """,
    re.VERBOSE,
)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        next_month = _dt.date(year + 1, 1, 1)
    else:
        next_month = _dt.date(year, month + 1, 1)
    this_month = _dt.date(year, month, 1)
    return (next_month - this_month).days


def _add_months(year: int, month: int, months_to_add: int) -> Tuple[int, int]:
    total = (year * 12 + (month - 1)) + months_to_add
    new_year = total // 12
    new_month = (total % 12) + 1
    return new_year, new_month


def _clamp_day(year: int, month: int, day: int) -> int:
    dim = _days_in_month(year, month)
    return min(day, dim)


def parse_iso8601(text: str, *, strict: bool = False) -> Dict[str, Any]:
    s = text.strip()
    m = _ISO_RE.match(s)
    if not m:
        raise ValueError(f"Invalid ISO-8601 datetime: {text!r}")

    gd = m.groupdict()
    year = int(gd["year"])
    month = int(gd["month"])
    day = int(gd["day"])

    if gd["hour"] is None:
        return {
            "year": year,
            "month": month,
            "day": day,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "microsecond": 0,
            "tz": None,
            "has_time": False,
        }

    hour = int(gd["hour"])
    minute = int(gd["minute"] or "00")
    second = int(gd["second"] or "00")

    frac = gd["fraction"] or ""
    if frac:
        micro = int(frac.ljust(6, "0"))
    else:
        micro = 0

    tz = gd["tz"]
    if strict:
        # In strict mode require full HH:MM and seconds if time is present.
        # Keep minimal: enforce presence of minute if hour exists.
        if gd["minute"] is None:
            raise ValueError(f"Invalid ISO-8601 datetime (strict): {text!r}")

    return {
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "minute": minute,
        "second": second,
        "microsecond": micro,
        "tz": tz,
        "has_time": True,
    }


def now(tz: Optional[_dt.tzinfo] = None) -> _dt.datetime:
    if tz is None:
        return _dt.datetime.now()
    return _dt.datetime.now(tz=tz)