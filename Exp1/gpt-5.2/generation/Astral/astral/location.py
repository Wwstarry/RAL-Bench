from __future__ import annotations

from dataclasses import dataclass
from datetime import tzinfo
from typing import Optional, Union

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


@dataclass(frozen=True)
class Observer:
    """Represents an observing position."""
    latitude: float
    longitude: float
    elevation: float = 0.0


@dataclass
class LocationInfo:
    """
    Minimal Astral-compatible location representation.

    Core fields in Astral:
      name, region, timezone, latitude, longitude
    Plus an .observer property with latitude/longitude/elevation.
    """
    name: str = "Greenwich"
    region: str = "England"
    timezone: str = "Europe/London"
    latitude: float = 51.4733
    longitude: float = 0.0

    @property
    def observer(self) -> Observer:
        # Astral's LocationInfo has an observer with elevation defaulting to 0.
        return Observer(latitude=float(self.latitude), longitude=float(self.longitude), elevation=0.0)

    @property
    def tzinfo(self) -> Optional[tzinfo]:
        if isinstance(self.timezone, str):
            if ZoneInfo is None:
                return None
            try:
                return ZoneInfo(self.timezone)
            except Exception:
                return None
        return None

    def __str__(self) -> str:
        return f"{self.name}/{self.region}, tz={self.timezone} ({self.latitude}, {self.longitude})"