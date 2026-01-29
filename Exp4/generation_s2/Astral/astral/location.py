from __future__ import annotations

from dataclasses import dataclass
from datetime import tzinfo
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Observer:
    """Geographic observer.

    Fields mirror Astral's Observer used by the public API.
    """
    latitude: float
    longitude: float
    elevation: float = 0.0


class LocationInfo:
    """Represents a named location.

    Minimal Astral-compatible surface:
      - name, region, timezone, latitude, longitude
      - .observer property returning an Observer instance
    """

    def __init__(
        self,
        name: str | None = None,
        region: str | None = None,
        timezone: str | tzinfo | None = "UTC",
        latitude: float = 0.0,
        longitude: float = 0.0,
    ) -> None:
        self.name = name or ""
        self.region = region or ""
        self.timezone = timezone or "UTC"
        self.latitude = float(latitude)
        self.longitude = float(longitude)

    @property
    def observer(self) -> Observer:
        return Observer(latitude=self.latitude, longitude=self.longitude, elevation=0.0)

    @property
    def tzinfo(self) -> tzinfo:
        tz = self.timezone
        if isinstance(tz, str):
            return ZoneInfo(tz)
        return tz

    def __repr__(self) -> str:
        return (
            f"LocationInfo(name={self.name!r}, region={self.region!r}, "
            f"timezone={self.timezone!r}, latitude={self.latitude!r}, longitude={self.longitude!r})"
        )