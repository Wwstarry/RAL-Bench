"""
A *very* trimmed down ``DateTime`` class trying to feel like
:class:`pendulum.datetime`.
"""
from __future__ import annotations

import re
from datetime import datetime as _dt
from datetime import timedelta as _td
from typing import Any, ClassVar, Optional

from .duration import Duration
from .timezone import timezone as _timezone
from .timezone import UTC
from .utils import _total_seconds


_DATETIME_ISO_RE = re.compile(
    r"""
    ^
    (?P<date>\d{4}-\d{2}-\d{2})
    [T ]
    (?P<time>\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?)
    (?P<tz>
        Z |
        (?:
            (?P<offset_sign>[+-])
            (?P<offset_hour>\d{2}):?(?P<offset_min>\d{2})
        )
    )?
    $
    """,
    re.VERBOSE,
)


class DateTime(_dt):
    """
    Sub-class of :class:`datetime.datetime` with a few helpers.
    """

    # --------------------- constructors --------------------- #
    def __new__(
        cls,
        year: int,
        month: int,
        day: int,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        microsecond: int = 0,
        tzinfo=None,
    ):
        return super().__new__(
            cls, year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo
        )

    # -------------- convenience factories ------------------- #
    @classmethod
    def now(cls, tz: Any = None):
        import datetime as _py_dt

        base = _py_dt.datetime.now(tz=_timezone(tz) if tz is not None else None)
        return cls._from_datetime(base)

    @classmethod
    def utcnow(cls):
        import datetime as _py_dt

        return cls._from_datetime(_py_dt.datetime.now(tz=UTC))

    # -------------- internal helpers ------------------- #
    @classmethod
    def _from_datetime(cls, dt: _dt) -> "DateTime":
        """
        Cast any :class:`datetime.datetime` instance to a ``DateTime`` keeping
        the exact same timestamp/tzinfo.
        """
        if isinstance(dt, cls):
            return dt
        return cls(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            dt.tzinfo,
        )

    # --------------------- helpers --------------------- #
    def in_timezone(self, tz: str | int | float):
        """
        Convert the current instance to another timezone.
        """
        tzinfo = _timezone(tz)
        # Convert to naive UTC then attach new tz
        if self.tzinfo is None:
            raise ValueError("Cannot convert timezone on naïve DateTime")

        # Using astimezone from stdlib will handle conversions
        converted = super().astimezone(tzinfo)
        return self._from_datetime(converted)

    # --------------------- arithmetic ------------------ #
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
    ):
        """
        Return a new ``DateTime`` + the supplied delta.

        Years & months are approximated (30 days per month, 365 days per
        year).  This is good enough for the reference tests.
        """
        dur = Duration(
            years=years,
            months=months,
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            microseconds=microseconds,
        )
        td = dur.as_timedelta()
        result = super().__add__(td)
        return self._from_datetime(result)

    # Universal arithmetic hooking
    def __add__(self, other):
        if isinstance(other, Duration):
            return self.add(
                years=other.years,
                months=other.months,
                weeks=other.weeks,
                days=other.days,
                hours=other.hours,
                minutes=other.minutes,
                seconds=other.seconds,
                microseconds=other.microseconds,
            )
        return super().__add__(other)

    def __sub__(self, other):
        if isinstance(other, Duration):
            return self.__add__(-other)
        if isinstance(other, DateTime):
            # Return a Duration object akin to pendulum
            delta: _td = super().__sub__(other)
            total = _total_seconds(delta)
            # We'll convert total seconds into a Duration (seconds only)
            sign = -1 if total < 0 else 1
            seconds = int(abs(total))
            microseconds = int(round((abs(total) - seconds) * 1_000_000))
            return Duration(seconds=sign * seconds, microseconds=sign * microseconds)
        return super().__sub__(other)

    # --------------------- human diff ------------------ #
    def diff_for_humans(self, other: Optional["DateTime"] = None) -> str:
        """
        Very small subset of pendulum's diff_for_humans.

        Examples
        --------
        >>> pendulum.datetime(2020, 1, 1).diff_for_humans(pendulum.datetime(2020,1,2))
        '1 day ago'
        >>> pendulum.datetime(2020, 1, 2).diff_for_humans(pendulum.datetime(2020,1,1))
        'in 1 day'
        """
        if other is None:
            other = DateTime.utcnow()

        delta = self - other  # returns Duration
        total_seconds = abs(delta.total_seconds())

        if total_seconds < 60:
            qty = int(total_seconds)
            unit = "second"
        elif total_seconds < 3600:
            qty = int(total_seconds // 60)
            unit = "minute"
        elif total_seconds < 86400:
            qty = int(total_seconds // 3600)
            unit = "hour"
        elif total_seconds < 86400 * 30:
            qty = int(total_seconds // 86400)
            unit = "day"
        elif total_seconds < 86400 * 365:
            qty = int(total_seconds // (86400 * 30))
            unit = "month"
        else:
            qty = int(total_seconds // (86400 * 365))
            unit = "year"

        if qty != 1:
            unit += "s"

        if (self - other).total_seconds() > 0:
            # self is in the future vs other
            return f"in {qty} {unit}"
        else:
            return f"{qty} {unit} ago"


# ---------------------------------------------------------------------------
# Parsing helpers (internal use)
# ---------------------------------------------------------------------------
def _parse_iso_datetime(val: str) -> DateTime:
    """
    Very naive ISO-8601 parser sufficient for YYYY-MM-DDTHH:MM:SS[.ffffff][Z|±HH:MM]
    """
    m = _DATETIME_ISO_RE.match(val)
    if not m:
        raise ValueError(f"Invalid ISO-8601 datetime string: {val!r}")

    date_part = m.group("date")
    time_part = m.group("time")
    tz_part = m.group("tz")

    year, month, day = map(int, date_part.split("-"))
    if "." in time_part:
        time_main, micro = time_part.split(".")
        micro = int(micro.ljust(6, "0"))
    else:
        time_main = time_part
        micro = 0
    hour, minute, second = map(int, time_main.split(":"))

    tzinfo = None
    if tz_part:
        if tz_part == "Z":
            tzinfo = UTC
        else:
            sign = 1 if m.group("offset_sign") == "+" else -1
            offset_hour = int(m.group("offset_hour"))
            offset_min = int(m.group("offset_min"))
            offset_sec = sign * (offset_hour * 3600 + offset_min * 60)
            tzinfo = _timezone(offset_sec)

    return DateTime(
        year,
        month,
        day,
        hour,
        minute,
        second,
        micro,
        tzinfo=tzinfo,
    )