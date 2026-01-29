"""
Very small & naïve *Duration* implementation.

This is **not** feature-parity with the real pendulum.Duration – it only carries
the operations required by the test-suite used for evaluation.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict

from .utils import _total_seconds


@dataclass(frozen=True)
class Duration:
    years: int = 0
    months: int = 0
    weeks: int = 0
    days: int = 0
    hours: int = 0
    minutes: int = 0
    seconds: int = 0
    microseconds: int = 0

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def as_timedelta(self) -> timedelta:
        """
        Convert the duration to a timedelta.  *Years* and *Months* are
        translated using a **rough** average of 30 days per month &
        365 days per year (the real pendulum uses more involved logic).
        """
        days = self.days + self.weeks * 7 + self.months * 30 + self.years * 365
        td = timedelta(
            days=days,
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds,
            microseconds=self.microseconds,
        )
        return td

    # ------------------------------------------------------------------ #
    # Magic methods
    # ------------------------------------------------------------------ #
    def __add__(self, other: "Duration") -> "Duration":
        if not isinstance(other, Duration):
            return NotImplemented
        return Duration(
            years=self.years + other.years,
            months=self.months + other.months,
            weeks=self.weeks + other.weeks,
            days=self.days + other.days,
            hours=self.hours + other.hours,
            minutes=self.minutes + other.minutes,
            seconds=self.seconds + other.seconds,
            microseconds=self.microseconds + other.microseconds,
        )

    def __sub__(self, other: "Duration") -> "Duration":
        if not isinstance(other, Duration):
            return NotImplemented
        return self + (-other)

    def __neg__(self) -> "Duration":
        return Duration(
            years=-self.years,
            months=-self.months,
            weeks=-self.weeks,
            days=-self.days,
            hours=-self.hours,
            minutes=-self.minutes,
            seconds=-self.seconds,
            microseconds=-self.microseconds,
        )

    def __mul__(self, factor: int | float) -> "Duration":
        if not isinstance(factor, (int, float)):
            return NotImplemented

        def round_int(x):
            return int(math.floor(x if x >= 0 else x - 0.5))

        return Duration(
            years=round_int(self.years * factor),
            months=round_int(self.months * factor),
            weeks=round_int(self.weeks * factor),
            days=round_int(self.days * factor),
            hours=round_int(self.hours * factor),
            minutes=round_int(self.minutes * factor),
            seconds=round_int(self.seconds * factor),
            microseconds=round_int(self.microseconds * factor),
        )

    __rmul__ = __mul__

    # ------------------------------------------------------------------ #
    # Numeric APIs
    # ------------------------------------------------------------------ #
    def total_seconds(self) -> float:
        """
        Alias for :pymeth:`datetime.timedelta.total_seconds` on the converted
        value.  Years & months use the coarse conversion described above.
        """
        return _total_seconds(self.as_timedelta())

    # ------------------------------------------------------------------ #
    # Representation
    # ------------------------------------------------------------------ #
    def _parts(self) -> Dict[str, int]:
        return {
            "years": self.years,
            "months": self.months,
            "weeks": self.weeks,
            "days": self.days,
            "hours": self.hours,
            "minutes": self.minutes,
            "seconds": self.seconds,
            "microseconds": self.microseconds,
        }

    def __repr__(self) -> str:
        parts = ", ".join(f"{k}={v}" for k, v in self._parts().items() if v)
        return f"{self.__class__.__name__}({parts or '0'})"