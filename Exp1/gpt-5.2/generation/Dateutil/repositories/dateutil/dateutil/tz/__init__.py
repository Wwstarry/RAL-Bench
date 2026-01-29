from __future__ import annotations

from datetime import tzinfo, timezone
import os
import time

__all__ = ["UTC", "gettz"]

UTC = timezone.utc


def gettz(name: str | None = None) -> tzinfo | None:
    """
    Minimal gettz implementation.

    Supports:
    - None => local timezone
    - 'UTC'/'GMT' => UTC
    - Offset forms like '+02:00', '-0500'
    - IANA names if the stdlib zoneinfo is available
    """
    if name is None:
        return _local_tz()

    if not isinstance(name, str):
        return None

    key = name.strip()
    if not key:
        return None
    up = key.upper()
    if up in ("UTC", "GMT", "Z"):
        return UTC

    # numeric offset
    off = _parse_offset(key)
    if off is not None:
        return off

    # Try zoneinfo (py3.9+)
    try:
        from zoneinfo import ZoneInfo  # type: ignore
    except Exception:
        ZoneInfo = None  # type: ignore

    if ZoneInfo is not None:
        try:
            return ZoneInfo(key)
        except Exception:
            return None

    return None


def _parse_offset(s: str):
    s = s.strip()
    if s == "Z":
        return UTC
    if len(s) in (5, 6) and (s[0] in "+-"):
        # +HHMM or +HH:MM
        sign = 1 if s[0] == "+" else -1
        if ":" in s:
            hh = int(s[1:3])
            mm = int(s[4:6])
        else:
            hh = int(s[1:3])
            mm = int(s[3:5])
        return timezone(sign * (hh * 3600 + mm * 60))
    return None


class _LocalTZ(timezone.__class__):  # type: ignore
    pass


def _local_tz():
    # Use time.timezone / time.altzone to build a fixed-offset tzinfo.
    # This won’t model DST transitions, but is sufficient for most tests.
    if time.daylight and time.localtime().tm_isdst > 0:
        offset = -time.altzone
    else:
        offset = -time.timezone
    return timezone(offset)