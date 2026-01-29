from __future__ import annotations

from dataclasses import dataclass
from datetime import tzinfo as _tzinfo
from datetime import timezone as _timezone
from datetime import timedelta
from typing import Optional

try:
    from zoneinfo import ZoneInfo  # py3.9+
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


@dataclass(frozen=True)
class Timezone:
    """
    Lightweight wrapper to match Pendulum's timezone objects.

    This wraps a stdlib tzinfo (zoneinfo.ZoneInfo or datetime.timezone).
    """
    name: str
    tzinfo: _tzinfo

    def __str__(self) -> str:  # pragma: no cover
        return self.name

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Timezone [{self.name}]>"


UTC = Timezone("UTC", _timezone.utc)


def timezone(name: str) -> Timezone:
    n = (name or "").strip()
    if n in ("UTC", "Z", "GMT"):
        return UTC

    # Offset like +02:00
    if (n.startswith("+") or n.startswith("-")) and len(n) >= 3:
        # defer parsing to utils
        from .utils import _coerce_tz
        tz = _coerce_tz(n)
        # tz here is datetime.timezone
        return Timezone(n, tz)

    if ZoneInfo is None:
        raise RuntimeError("zoneinfo is not available in this Python runtime")

    try:
        zi = ZoneInfo(n)
    except Exception as e:
        raise ValueError(f"Unknown timezone: {name!r}") from e
    return Timezone(n, zi)


def local_timezone() -> Timezone:
    from .utils import _system_local_tzinfo
    tz = _system_local_tzinfo()
    # Best effort name
    name = getattr(tz, "key", None) or getattr(tz, "tzname", lambda _=None: None)() or "local"
    return Timezone(str(name), tz)