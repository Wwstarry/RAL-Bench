from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Observer:
    latitude: float
    longitude: float
    elevation: float = 0.0


@dataclass(frozen=True)
class LocationInfo:
    """Represents a named location.

    Compatible with core usage in Astral:
      LocationInfo(name=..., region=..., timezone=..., latitude=..., longitude=...)
    """

    name: str = ""
    region: str = ""
    timezone: str = "UTC"
    latitude: float = 0.0
    longitude: float = 0.0
    elevation: float = 0.0

    @property
    def observer(self) -> Observer:
        return Observer(self.latitude, self.longitude, self.elevation)

    # Some code expects .tzinfo or similar; keep minimal but helpful.
    @property
    def tzinfo(self):
        try:
            from zoneinfo import ZoneInfo
        except Exception:  # pragma: no cover
            return None
        try:
            return ZoneInfo(self.timezone)
        except Exception:
            return None

    def __repr__(self) -> str:
        return (
            f"LocationInfo(name={self.name!r}, region={self.region!r}, "
            f"timezone={self.timezone!r}, latitude={self.latitude!r}, "
            f"longitude={self.longitude!r}, elevation={self.elevation!r})"
        )