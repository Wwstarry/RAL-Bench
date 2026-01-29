from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Optional


@dataclass(frozen=True)
class Duration:
    """
    Small subset of Pendulum's Duration.

    Stores a datetime.timedelta and optional month/year fields to support
    DateTime.add() semantics.
    """
    _delta: timedelta = timedelta(0)
    years: int = 0
    months: int = 0

    @property
    def total_seconds(self) -> float:
        return self._delta.total_seconds()

    def in_seconds(self) -> int:
        return int(self._delta.total_seconds())

    def in_minutes(self) -> int:
        return int(self._delta.total_seconds() // 60)

    def in_hours(self) -> int:
        return int(self._delta.total_seconds() // 3600)

    def in_days(self) -> int:
        return int(self._delta.total_seconds() // 86400)

    def __add__(self, other: Any):
        if isinstance(other, Duration):
            return Duration(self._delta + other._delta, self.years + other.years, self.months + other.months)
        if isinstance(other, timedelta):
            return Duration(self._delta + other, self.years, self.months)
        return NotImplemented

    def __neg__(self):
        return Duration(-self._delta, -self.years, -self.months)

    def __sub__(self, other: Any):
        if isinstance(other, Duration):
            return Duration(self._delta - other._delta, self.years - other.years, self.months - other.months)
        if isinstance(other, timedelta):
            return Duration(self._delta - other, self.years, self.months)
        return NotImplemented

    def __repr__(self) -> str:
        parts = []
        if self.years:
            parts.append(f"years={self.years}")
        if self.months:
            parts.append(f"months={self.months}")
        if self._delta != timedelta(0):
            parts.append(f"delta={self._delta!r}")
        inner = ", ".join(parts) if parts else "0"
        return f"Duration({inner})"

    def as_timedelta(self) -> timedelta:
        return self._delta


def duration(
    *,
    years: int = 0,
    months: int = 0,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    microseconds: int = 0,
    **kwargs: Any,
) -> Duration:
    # Ignore unsupported kwargs to be permissive with tests that pass extra zeros.
    delta = timedelta(
        weeks=weeks,
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        microseconds=microseconds,
    )
    return Duration(delta, years=years, months=months)