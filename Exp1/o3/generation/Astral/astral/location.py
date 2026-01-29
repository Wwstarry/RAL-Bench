from __future__ import annotations

import dataclasses
from typing import Optional
from datetime import tzinfo
from zoneinfo import ZoneInfo


@dataclasses.dataclass(frozen=True)
class Observer:
    """
    A minimal replacement for astral's Observer.

    Attributes
    ----------
    latitude  : float – Degrees North (negative south)
    longitude : float – Degrees East  (negative west)
    elevation : float – Metres above sea-level
    """

    latitude: float
    longitude: float
    elevation: float = 0.0


@dataclasses.dataclass
class LocationInfo:
    """
    A lightweight container for an observer with some metadata attached.

    Parameters
    ----------
    name      : str   – Human readable name (e.g. “London”)
    region    : str   – Region/Country (e.g. “England”)
    timezone  : str   – IANA timezone name (e.g. “Europe/London”)
    latitude  : float – Decimal degrees
    longitude : float – Decimal degrees
    """

    name: str
    region: str
    timezone: str
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        # Fail early for bogus time-zones
        try:
            ZoneInfo(self.timezone)
        except Exception as exc:  # pragma: no cover
            raise ValueError(f"Invalid timezone '{self.timezone}': {exc}") from exc

    # ------------------------------------------------------------------ #
    # Public helpers
    # ------------------------------------------------------------------ #
    @property
    def tzinfo(self) -> tzinfo:
        """Return `zoneinfo.ZoneInfo` object for the location's timezone."""
        return ZoneInfo(self.timezone)

    # Astral exposes an “observer” attribute with lat/lon/elev
    @property
    def observer(self) -> Observer:
        """Return an `Observer` view of the location."""
        return Observer(self.latitude, self.longitude, 0.0)

    # String helpers
    # --------------
    def __iter__(self):
        yield from (self.name, self.region, self.timezone, self.latitude, self.longitude)

    def __repr__(self) -> str:  # pragma: no cover
        klass = self.__class__.__name__
        return (
            f"{klass}(name={self.name!r}, region={self.region!r}, "
            f"timezone={self.timezone!r}, latitude={self.latitude}, "
            f"longitude={self.longitude})"
        )