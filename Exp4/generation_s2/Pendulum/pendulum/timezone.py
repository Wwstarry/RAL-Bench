from __future__ import annotations

from datetime import timezone as _dt_timezone, timedelta
from typing import Any, Optional, Union

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


UTC = _dt_timezone.utc


def timezone(name: Union[str, Any]):
    """
    Return a tzinfo for the given name.

    Supports:
    - "UTC"
    - IANA names via zoneinfo.ZoneInfo (tzdata dependency provides data)
    - fixed offsets like "+02:00", "-0530", "+00"
    - passing through existing tzinfo objects
    """
    if name is None:
        return None
    if hasattr(name, "utcoffset") and not isinstance(name, str):
        return name
    if isinstance(name, str):
        n = name.strip()
        if n.upper() in ("UTC", "Z"):
            return UTC

        # Fixed offset formats
        if n.startswith(("+", "-")):
            sign = 1 if n[0] == "+" else -1
            rest = n[1:]
            hours = 0
            minutes = 0
            if ":" in rest:
                h, m = rest.split(":", 1)
                hours = int(h or "0")
                minutes = int(m or "0")
            else:
                if len(rest) <= 2:
                    hours = int(rest or "0")
                    minutes = 0
                elif len(rest) == 4:
                    hours = int(rest[:2])
                    minutes = int(rest[2:])
                else:
                    # Best effort
                    hours = int(rest[:2])
                    minutes = int(rest[2:4] or "0")
            delta = timedelta(hours=hours, minutes=minutes) * sign
            return _dt_timezone(delta)

        # IANA via zoneinfo
        if ZoneInfo is None:
            raise ValueError("zoneinfo not available in this environment")
        try:
            return ZoneInfo(n)
        except Exception as e:
            raise ValueError(f"Invalid timezone {name!r}") from e

    raise TypeError(f"Invalid timezone {name!r}")


def local_timezone():
    # stdlib has no robust cross-platform local tz; fall back to system tzinfo
    # from current time.
    from datetime import datetime as _dt_datetime

    return _dt_datetime.now().astimezone().tzinfo


def _tz_name(tz) -> str:
    if tz is None:
        return "naive"
    if tz is UTC:
        return "UTC"
    key = getattr(tz, "key", None)
    if isinstance(key, str):
        return key
    return str(tz)