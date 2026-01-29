"""
Very small helper utilities for dealing with *tzinfo* objects.

We piggy-back on the standard library's ``zoneinfo`` implementation available
since CPython 3.9.  When it is missing we gracefully fall back to the fixed
offset support from ``datetime.timezone``.
"""
from __future__ import annotations

import math
import sys
from datetime import timezone as _fixed, timedelta as _td
from types import MappingProxyType
from typing import Any

try:
    from zoneinfo import ZoneInfo  # pragma: no cover – only available >=3.9
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
UTC = _fixed.utc
_LOCAL_CACHE: dict[str, Any] = {  # cache instances to avoid waste
    "UTC": UTC,
}


def _fixed_offset(offset_seconds: int):
    """
    Return a *fixed* offset tzinfo.
    """
    if offset_seconds == 0:
        return UTC
    name = f"UTC{'+' if offset_seconds >= 0 else ''}{offset_seconds // 3600:02d}"
    return _fixed(_td(seconds=offset_seconds), name)


def timezone(tz: str | int | float | None = None):
    """
    Convert the *tz* specifier to a proper ``tzinfo`` implementation.

    *tz* accepted values:
      * ``None`` –> UTC
      * ``str``  –> resolved through ``zoneinfo.ZoneInfo``
      * number   –> treated as *seconds* offset from UTC
    """
    if tz is None:
        return UTC

    # ------------------------------------------------------------------ #
    # Numeric offset
    # ------------------------------------------------------------------ #
    if isinstance(tz, (int, float)):
        offset = int(math.floor(tz))
        return _fixed_offset(offset)

    # ------------------------------------------------------------------ #
    # String => ZoneInfo
    # ------------------------------------------------------------------ #
    if not isinstance(tz, str):
        raise TypeError("tz must be None | str | int | float")

    if tz in _LOCAL_CACHE:
        return _LOCAL_CACHE[tz]

    if ZoneInfo is not None:
        try:
            obj = ZoneInfo(tz)
        except Exception:
            raise ValueError(f"Unknown timezone '{tz}'") from None
    else:  # zoneinfo missing, fallback to UTC only
        if tz.upper() in ("UTC", "Z"):
            obj = UTC
        else:
            raise ValueError("Named timezones require Python >=3.9")

    _LOCAL_CACHE[tz] = obj
    return obj