from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Any, Optional


def _normalize_fixed(
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    microseconds: int = 0,
) -> tuple[int, int, int, int, int, int]:
    td = _dt.timedelta(
        weeks=weeks,
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        microseconds=microseconds,
    )
    total_us = td.days * 86400 * 1_000_000 + td.seconds * 1_000_000 + td.microseconds

    sign = -1 if total_us < 0 else 1
    total_us = abs(total_us)

    us = total_us % 1_000_000
    total_s = total_us // 1_000_000
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    total_h = total_m // 60
    h = total_h % 24
    total_d = total_h // 24
    # keep weeks split out for nicer repr/attrs
    w = total_d // 7
    d = total_d % 7

    return (sign * w, sign * d, sign * h, sign * m, sign * s, sign * us)


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

    def as_timedelta(self) -> _dt.timedelta:
        return _dt.timedelta(
            weeks=self.weeks,
            days=self.days,
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds,
            microseconds=self.microseconds,
        )

    def total_seconds(self) -> float:
        return self.as_timedelta().total_seconds()

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

    def __add__(self, other: Any):
        if isinstance(other, _dt.timedelta):
            td = self.as_timedelta() + other
            return Duration(
                years=self.years,
                months=self.months,
                weeks=0,
                days=td.days,
                seconds=td.seconds,
                microseconds=td.microseconds,
            )
        if isinstance(other, Duration):
            td = self.as_timedelta() + other.as_timedelta()
            return Duration(
                years=self.years + other.years,
                months=self.months + other.months,
                weeks=0,
                days=td.days,
                seconds=td.seconds,
                microseconds=td.microseconds,
            )
        return NotImplemented

    def __radd__(self, other: Any):
        # DateTime handles addition; support timedelta + Duration
        if isinstance(other, _dt.timedelta):
            return self.__add__(other)
        return NotImplemented

    def __sub__(self, other: Any):
        if isinstance(other, Duration):
            return self + (-other)
        if isinstance(other, _dt.timedelta):
            return self + (-Duration(days=other.days, seconds=other.seconds, microseconds=other.microseconds))
        return NotImplemented

    def __repr__(self) -> str:
        parts = []
        for k in ("years", "months", "weeks", "days", "hours", "minutes", "seconds", "microseconds"):
            v = getattr(self, k)
            if v:
                parts.append(f"{k}={v}")
        inner = ", ".join(parts) if parts else "0"
        return f"Duration({inner})"


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
) -> Duration:
    w, d, h, m, s, us = _normalize_fixed(weeks, days, hours, minutes, seconds, microseconds)
    return Duration(
        years=years,
        months=months,
        weeks=w,
        days=d,
        hours=h,
        minutes=m,
        seconds=s,
        microseconds=us,
    )