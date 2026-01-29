# pendulum/timezone.py
from __future__ import annotations

from datetime import tzinfo

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:
    # Fallback for Python < 3.9. A real implementation would vendor
    # `backports.zoneinfo`. For this exercise, we assume a modern Python.
    raise ImportError(
        "The 'zoneinfo' module is required. "
        "Please use Python 3.9+ or install 'backports.zoneinfo'."
    )

_tz_cache: dict[str, Timezone] = {}


class Timezone(tzinfo):
    """
    A timezone object.
    """

    def __init__(self, name: str) -> None:
        try:
            # Normalize common case
            if name.upper() == "UTC":
                name = "UTC"
            self._tz = ZoneInfo(name)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Unknown timezone '{name}'")
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def utcoffset(self, dt):
        return self._tz.utcoffset(dt)

    def dst(self, dt):
        return self._tz.dst(dt)

    def tzname(self, dt):
        return self._tz.tzname(dt)

    def __repr__(self) -> str:
        return f"Timezone('{self.name}')"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Timezone):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)


def timezone(name: str) -> Timezone:
    """
    Returns a Timezone instance for a given timezone name.
    """
    if name not in _tz_cache:
        _tz_cache[name] = Timezone(name)

    return _tz_cache[name]


UTC = timezone("UTC")