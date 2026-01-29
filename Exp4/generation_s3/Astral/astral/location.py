from __future__ import annotations

from dataclasses import dataclass

from .types import Observer


@dataclass
class LocationInfo:
    """A simple container describing a named location."""

    name: str = ""
    region: str = ""
    timezone: str = "UTC"
    latitude: float = 0.0
    longitude: float = 0.0

    @property
    def observer(self) -> Observer:
        # Astral exposes an Observer-like object at .observer
        return Observer(latitude=float(self.latitude), longitude=float(self.longitude), elevation=0.0)