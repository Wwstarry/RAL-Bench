from __future__ import annotations

import re
from datetime import datetime as _dt
from datetime import timedelta, timezone as _timezone
from typing import Any, Optional, Union

from .duration import Duration, duration as _duration
from .utils import _coerce_tz, _is_aware, _round_timedelta_seconds


class DateTime(_dt):
    """
    Subclass of datetime.datetime with a small subset of Pendulum's API.
    """

    # ---- Constructors ----
    @classmethod
    def instance(cls, dt: _dt) -> "DateTime":
        if isinstance(dt, DateTime):
            return dt
        return cls(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            tzinfo=dt.tzinfo,
            fold=getattr(dt, "fold", 0),
        )

    # ---- Pendulum-like API ----
    def in_timezone(self, tz: Union[str, Any]) -> "DateTime":
        tzinfo = _coerce_tz(tz)
        if tzinfo is None:
            # naive requested: drop tzinfo
            return DateTime(
                self.year,
                self.month,
                self.day,
                self.hour,
                self.minute,
                self.second,
                self.microsecond,
                tzinfo=None,
                fold=getattr(self, "fold", 0),
            )
        if not _is_aware(self):
            # Assume naive datetime is in requested timezone and just attach it.
            return DateTime(
                self.year,
                self.month,
                self.day,
                self.hour,
                self.minute,
                self.second,
                self.microsecond,
                tzinfo=tzinfo,
                fold=getattr(self, "fold", 0),
            )
        converted = self.astimezone(tzinfo)
        return DateTime.instance(converted)

    def add(
        self,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0,
    ) -> "DateTime":
        # years/months calendar arithmetic; rest as timedelta.
        y = self.year + years
        m = self.month + months
        while m > 12:
            y += 1
            m -= 12
        while m < 1:
            y -= 1
            m += 12

        d = min(self.day, _days_in_month(y, m))
        base = DateTime(
            y,
            m,
            d,
            self.hour,
            self.minute,
            self.second,
            self.microsecond,
            tzinfo=self.tzinfo,
            fold=getattr(self, "fold", 0),
        )
        delta = timedelta(
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            microseconds=microseconds,
        )
        return DateTime.instance(base + delta)

    def diff_for_humans(
        self,
        other: Optional[Union[_dt, "DateTime"]] = None,
        absolute: bool = False,
    ) -> str:
        if other is None:
            other = _dt.now(tz=self.tzinfo) if self.tzinfo else _dt.now()
        other_dt = DateTime.instance(other)

        diff = self - other_dt  # Duration
        seconds = diff.total_seconds()
        past = seconds < 0
        seconds = abs(seconds)

        # thresholds similar to common humanization:
        if seconds < 5:
            text = "just now"
            return text if absolute else text

        units = [
            ("year", 365 * 24 * 3600),
            ("month", 30 * 24 * 3600),
            ("week", 7 * 24 * 3600),
            ("day", 24 * 3600),
            ("hour", 3600),
            ("minute", 60),
            ("second", 1),
        ]

        count = 0
        unit_name = "second"
        for name, size in units:
            if seconds >= size:
                count = int(seconds // size)
                unit_name = name
                break

        if count == 1:
            phrase = f"1 {unit_name}"
        else:
            phrase = f"{count} {unit_name}s"

        if absolute:
            return phrase

        if past:
            return f"{phrase} ago"
        return f"in {phrase}"

    # Make subtraction produce Duration
    def __sub__(self, other):
        if isinstance(other, _dt):
            td = super().__sub__(other)
            return Duration.from_timedelta(td)
        if isinstance(other, timedelta):
            return DateTime.instance(super().__sub__(other))
        return NotImplemented

    def __add__(self, other):
        if isinstance(other, timedelta):
            return DateTime.instance(super().__add__(other))
        if isinstance(other, Duration):
            return DateTime.instance(super().__add__(other.as_timedelta()))
        return NotImplemented


def datetime(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    microsecond: int = 0,
    tz: Optional[Union[str, Any]] = None,
) -> DateTime:
    tzinfo = _coerce_tz(tz)
    return DateTime(year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)


def now(tz: Optional[Union[str, Any]] = None) -> DateTime:
    tzinfo = _coerce_tz(tz)
    return DateTime.instance(_dt.now(tz=tzinfo))


_ISO_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})"
    r"(?:[T ](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,9}))?)?)?"
    r"(?:Z|([+-]\d{2}:?\d{2}|[+-]\d{2}))?$"
)


def parse(text: str, tz: Optional[Union[str, Any]] = None) -> DateTime:
    s = text.strip()
    m = _ISO_RE.match(s)
    if not m:
        # Fallback to fromisoformat (may raise)
        dt = _dt.fromisoformat(s.replace("Z", "+00:00"))
        if tz is not None:
            return DateTime.instance(dt).in_timezone(tz)
        return DateTime.instance(dt)

    year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
    hh = int(m.group(4) or 0)
    mm = int(m.group(5) or 0)
    ss = int(m.group(6) or 0)
    frac = m.group(7) or ""
    us = 0
    if frac:
        frac = (frac + "000000")[:6]
        us = int(frac)
    offset = m.group(8)

    if s.endswith("Z"):
        tzinfo = _timezone.utc
    elif offset:
        tzinfo = _coerce_tz(offset)
    else:
        tzinfo = None

    dt = DateTime(year, month, day, hh, mm, ss, us, tzinfo=tzinfo)

    if tz is not None:
        return dt.in_timezone(tz)
    return dt


def _days_in_month(year: int, month: int) -> int:
    if month == 2:
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return 29
        return 28
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31
    return 30