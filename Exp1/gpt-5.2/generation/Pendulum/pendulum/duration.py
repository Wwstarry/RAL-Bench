from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional


@dataclass(frozen=True)
class Duration:
    """
    A minimal duration compatible with timedelta with Pendulum-like API.
    Internally stores total microseconds as a timedelta.
    """
    _delta: timedelta

    @classmethod
    def from_timedelta(cls, td: timedelta) -> "Duration":
        return cls(td)

    @property
    def total_seconds(self) -> float:
        return self._delta.total_seconds()

    @property
    def days(self) -> int:
        return self._delta.days

    @property
    def seconds(self) -> int:
        return self._delta.seconds

    @property
    def microseconds(self) -> int:
        return self._delta.microseconds

    def as_timedelta(self) -> timedelta:
        return self._delta

    def __add__(self, other):
        if isinstance(other, Duration):
            return Duration(self._delta + other._delta)
        if isinstance(other, timedelta):
            return Duration(self._delta + other)
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Duration):
            return Duration(self._delta - other._delta)
        if isinstance(other, timedelta):
            return Duration(self._delta - other)
        return NotImplemented

    def __neg__(self):
        return Duration(-self._delta)

    def __abs__(self):
        return Duration(abs(self._delta))

    def __repr__(self) -> str:  # pragma: no cover
        return f"Duration({self._delta!r})"


def duration(
    *,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    microseconds: int = 0,
) -> Duration:
    return Duration(
        timedelta(
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            microseconds=microseconds,
        )
    )