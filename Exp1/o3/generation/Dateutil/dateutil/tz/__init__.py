"""
Simplified replacement for `dateutil.tz`.

Only a handful of features needed by the tests are implemented:
    * :data:`UTC` – singleton UTC tzinfo.
    * :func:`gettz` – retrieve IANA time zones via ``zoneinfo.ZoneInfo`` or
      simple fixed-offset fallbacks for 'UTC', 'GMT', etc.
    * :class:`tzoffset` – fixed offset tzinfo for arbitrary offsets.
"""
from __future__ import annotations

import datetime as _dt
from typing import Optional

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore


class _UTC(_dt.tzinfo):
    """UTC as a singleton tzinfo – mimics ``dateutil.tz.tzutc``."""

    __slots__ = ()

    def __repr__(self):
        return "tzutc()"

    def utcoffset(self, dt):
        return _dt.timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return _dt.timedelta(0)


UTC = _UTC()


class tzoffset(_dt.tzinfo):
    """Fixed numeric offset time-zone."""

    def __init__(self, name: str, offset: int):
        self._offset_seconds = int(offset)
        self._name = name

    def utcoffset(self, dt):
        return _dt.timedelta(seconds=self._offset_seconds)

    def dst(self, dt):
        return _dt.timedelta(0)

    def tzname(self, dt):
        return self._name

    def __repr__(self):
        return f"tzoffset({self._name!r}, {self._offset_seconds})"


def gettz(name: Optional[str] = None) -> Optional[_dt.tzinfo]:
    """
    Retrieve a time-zone object for the given *name*.

    The implementation prefers the new stdlib ``zoneinfo`` module when
    available.  For the special case of ``'UTC'``/``'GMT'`` a singleton UTC
    object is returned.  If the zone cannot be found, *None* is returned to
    mirror ``dateutil`` behaviour.
    """
    if name is None:
        return None
    if name.upper() in {"UTC", "Z", "GMT"}:
        return UTC
    if ZoneInfo is not None:
        try:
            return ZoneInfo(key=name)
        except Exception:
            return None
    return None