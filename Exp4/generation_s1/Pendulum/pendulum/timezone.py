from __future__ import annotations

import datetime as _dt
import re
from typing import Optional, Union

try:
    from zoneinfo import ZoneInfo  # type: ignore
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

UTC = _dt.timezone.utc

_OFFSET_RE = re.compile(
    r"""
    ^
    (?P<sign>[+-])
    (?P<hours>\d{2})
    (?:
        :?(?P<minutes>\d{2})
    )?
    $
    """,
    re.VERBOSE,
)


def _parse_offset(value: str) -> int:
    """
    Parse offsets like +02, +0200, +02:00, -0530 into minutes.
    """
    s = value.strip()
    if s in ("Z", "UTC"):
        return 0

    m = _OFFSET_RE.match(s)
    if not m:
        raise ValueError(f"Invalid timezone offset: {value!r}")

    sign = -1 if m.group("sign") == "-" else 1
    hours = int(m.group("hours"))
    minutes = int(m.group("minutes") or "00")
    if hours > 23 or minutes > 59:
        raise ValueError(f"Invalid timezone offset: {value!r}")
    return sign * (hours * 60 + minutes)


def fixed_timezone(minutes: int) -> _dt.tzinfo:
    return _dt.timezone(_dt.timedelta(minutes=minutes))


def _local_timezone() -> _dt.tzinfo:
    # Best-effort local tzinfo; deterministic fallback to UTC.
    try:
        return _dt.datetime.now().astimezone().tzinfo or UTC
    except Exception:  # pragma: no cover
        return UTC


def timezone(value: Optional[Union[str, int, _dt.tzinfo]] = None) -> _dt.tzinfo:
    """
    Factory compatible with a subset of Pendulum's timezone().

    Accepts:
    - None: local timezone (best effort; fallback UTC)
    - "UTC"/"Z": UTC
    - IANA name: "Europe/Paris"
    - offset strings: "+02:00", "-0530", "+05"
    - int: minutes offset
    - tzinfo: returned as-is
    """
    if value is None:
        return _local_timezone()

    if isinstance(value, _dt.tzinfo):
        return value

    if isinstance(value, int):
        return fixed_timezone(value)

    if not isinstance(value, str):
        raise TypeError(f"Invalid timezone: {value!r}")

    name = value.strip()
    if name in ("UTC", "Z"):
        return UTC

    # Offset formats
    if name.startswith(("+", "-")):
        minutes = _parse_offset(name)
        if minutes == 0:
            return UTC
        return fixed_timezone(minutes)

    # IANA zone
    if ZoneInfo is None:  # pragma: no cover
        raise ValueError("ZoneInfo is not available in this Python environment")

    try:
        return ZoneInfo(name)
    except Exception as e:
        raise ValueError(f"Unknown timezone {name!r}") from e