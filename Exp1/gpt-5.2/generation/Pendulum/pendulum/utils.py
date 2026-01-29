from __future__ import annotations

import re
from datetime import datetime as _dt
from datetime import timezone as _timezone
from datetime import timedelta
from typing import Optional, Union


TZ_ALIASES = {
    "UTC": "UTC",
    "Z": "UTC",
    "GMT": "UTC",
}


def _system_local_tzinfo():
    # Uses stdlib's local timezone detection.
    return _dt.now().astimezone().tzinfo


def _coerce_tz(tz) -> Optional[object]:
    """
    Coerce a tz input into a tzinfo-compatible object.

    Supported forms:
      - None
      - "UTC", "Z", "GMT"
      - "+HH:MM", "-HHMM", "+HH"
      - datetime.tzinfo (including zoneinfo.ZoneInfo)
      - pendulum.timezone.Timezone (wrapper)
    """
    if tz is None:
        return None

    # Avoid circular imports
    from .timezone import Timezone, timezone as _pz_timezone

    if isinstance(tz, Timezone):
        return tz.tzinfo

    if hasattr(tz, "utcoffset") and hasattr(tz, "dst"):
        return tz

    if isinstance(tz, str):
        t = tz.strip()
        t = TZ_ALIASES.get(t, t)
        if t in ("UTC",):
            return _timezone.utc

        # ISO offset like +02:00, -0530, +02
        m = re.fullmatch(r"([+-])(\d{2})(?::?(\d{2}))?$", t)
        if m:
            sign = 1 if m.group(1) == "+" else -1
            hh = int(m.group(2))
            mm = int(m.group(3) or 0)
            return _timezone(sign * timedelta(hours=hh, minutes=mm))

        # IANA zone
        return _pz_timezone(t).tzinfo

    raise TypeError(f"Invalid timezone: {tz!r}")


def _isoformat_offset(tzinfo, dt: _dt) -> str:
    if tzinfo is None:
        return ""
    off = tzinfo.utcoffset(dt)
    if off is None:
        return ""
    total = int(off.total_seconds())
    if total == 0:
        return "+00:00"
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    hh = total // 3600
    mm = (total % 3600) // 60
    return f"{sign}{hh:02d}:{mm:02d}"


def _is_aware(dt: _dt) -> bool:
    return dt.tzinfo is not None and dt.utcoffset() is not None


def _round_timedelta_seconds(seconds: float) -> int:
    # For humanization thresholds we want deterministic rounding.
    # Use int truncation toward zero.
    return int(seconds)