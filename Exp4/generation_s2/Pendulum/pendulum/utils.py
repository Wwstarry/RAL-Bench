from __future__ import annotations

from datetime import datetime as _dt_datetime, timezone as _dt_timezone
from typing import Any, Optional


def _as_timezone(tz: Any):
    # Imported lazily to avoid circular imports
    from .timezone import timezone as _pendulum_timezone, UTC

    if tz is None:
        return None
    if tz is UTC:
        return UTC
    if isinstance(tz, str):
        return _pendulum_timezone(tz)
    # Support datetime.timezone, zoneinfo, tzinfo instances
    return tz


def _system_utc_offset_minutes(d: _dt_datetime) -> int:
    """Return system offset (in minutes) for provided aware datetime."""
    off = d.utcoffset()
    if off is None:
        return 0
    return int(off.total_seconds() // 60)


def _coerce_to_datetime(value: Any) -> _dt_datetime:
    if isinstance(value, _dt_datetime):
        return value
    raise TypeError(f"Expected datetime, got {type(value)!r}")


def _ensure_aware(dt: _dt_datetime, tz: Optional[Any] = None) -> _dt_datetime:
    """Ensure datetime is timezone-aware. If naive, attach tz or UTC."""
    if dt.tzinfo is not None:
        return dt
    if tz is None:
        tz = _dt_timezone.utc
    return dt.replace(tzinfo=tz)


def _sign(n: int) -> int:
    return -1 if n < 0 else (1 if n > 0 else 0)