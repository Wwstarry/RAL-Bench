# pendulum/datetime.py
from __future__ import annotations

import datetime as dt

from .duration import Duration
from .timezone import Timezone, timezone as get_timezone, UTC
from .utils import _add_months

# Constants
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
MONTHS_PER_YEAR = 12


class DateTime(dt.datetime):
    """
    A replacement for the standard datetime object.
    """

    def __new__(
        cls,
        year: int,
        month: int,
        day: int,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        microsecond: int = 0,
        tzinfo: dt.tzinfo | None = None,
        *,
        fold: int = 0,
    ) -> DateTime:
        if isinstance(tzinfo, str):
            tzinfo = get_timezone(tzinfo)
        return super().__new__(
            cls, year, month, day, hour, minute, second, microsecond, tzinfo, fold=fold
        )

    def in_timezone(self, tz: str | Timezone) -> DateTime:
        """
        Set the timezone of the datetime.
        """
        if isinstance(tz, str):
            tz = get_timezone(tz)

        new_dt = self.astimezone(tz)
        return self.__class__(
            new_dt.year,
            new_dt.month,
            new_dt.day,
            new_dt.hour,
            new_dt.minute,
            new_dt.second,
            new_dt.microsecond,
            tzinfo=new_dt.tzinfo,
        )

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
    ) -> DateTime:
        """
        Adds a duration to the datetime.
        """
        dt = self
        if years:
            dt = _add_months(dt, years * MONTHS_PER_YEAR)
        if months:
            dt = _add_months(dt, months)

        duration = dt.timedelta(
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            microseconds=microseconds,
        )

        new_dt = super(DateTime, dt).__add__(duration)
        return self.__class__(
            new_dt.year,
            new_dt.month,
            new_dt.day,
            new_dt.hour,
            new_dt.minute,
            new_dt.second,
            new_dt.microsecond,
            tzinfo=new_dt.tzinfo,
        )

    def subtract(
        self,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0,
    ) -> DateTime:
        """
        Subtracts a duration from the datetime.
        """
        return self.add(
            years=-years,
            months=-months,
            weeks=-weeks,
            days=-days,
            hours=-hours,
            minutes=-minutes,
            seconds=-seconds,
            microseconds=-microseconds,
        )

    def __add__(self, other: dt.timedelta) -> DateTime:
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
        if isinstance(other, dt.timedelta):
            new_dt = super().__add__(other)
            return self.__class__(
                new_dt.year,
                new_dt.month,
                new_dt.day,
                new_dt.hour,
                new_dt.minute,
                new_dt.second,
                new_dt.microsecond,
                tzinfo=self.tzinfo,
            )
        return NotImplemented

    def __sub__(self, other: dt.datetime | dt.timedelta) -> DateTime | Duration:
        if isinstance(other, dt.datetime):
            # Pendulum returns a Period (our Duration).
            # This is a simplified diff that doesn't calculate years/months.
            if self.tzinfo is None or other.tzinfo is None:
                # For naive datetimes, perform naive subtraction
                td = super().__sub__(other)
            else:
                # For aware datetimes, ensure they are in the same timezone
                td = self.astimezone(UTC) - other.astimezone(UTC)

            return Duration(seconds=td.total_seconds())

        if isinstance(other, Duration):
            return self.subtract(
                years=other.years,
                months=other.months,
                weeks=other.weeks,
                days=other.days,
                hours=other.hours,
                minutes=other.minutes,
                seconds=other.seconds,
                microseconds=other.microseconds,
            )
        if isinstance(other, dt.timedelta):
            new_dt = super().__sub__(other)
            return self.__class__(
                new_dt.year,
                new_dt.month,
                new_dt.day,
                new_dt.hour,
                new_dt.minute,
                new_dt.second,
                new_dt.microsecond,
                tzinfo=self.tzinfo,
            )
        return NotImplemented

    def diff_for_humans(self, other: DateTime | None = None, absolute: bool = False, locale: str | None = None) -> str:
        """
        Get the difference in a human readable format.
        """
        if other is None:
            other = self.__class__.now(self.tzinfo)

        is_future = self > other

        if is_future:
            diff = self - other
        else:
            diff = other - self

        s = diff.total_seconds()

        if s < 1:
            return "just now"
        if s < SECONDS_PER_MINUTE:
            value = int(s)
            unit = "second"
        elif s < SECONDS_PER_HOUR:
            value = int(s / SECONDS_PER_MINUTE)
            unit = "minute"
        elif s < SECONDS_PER_DAY:
            value = int(s / SECONDS_PER_HOUR)
            unit = "hour"
        elif s < SECONDS_PER_DAY * 7:
            value = int(s / SECONDS_PER_DAY)
            unit = "day"
        elif s < SECONDS_PER_DAY * 30.4375:  # Average month length
            value = int(s / (SECONDS_PER_DAY * 7))
            unit = "week"
        elif s < SECONDS_PER_DAY * 365.25:  # Average year length
            value = int(s / (SECONDS_PER_DAY * 30.4375))
            unit = "month"
        else:
            value = int(s / (SECONDS_PER_DAY * 365.25))
            unit = "year"

        plural = "s" if value > 1 else ""

        if absolute:
            return f"{value} {unit}{plural}"

        if is_future:
            return f"in {value} {unit}{plural}"
        else:
            return f"{value} {unit}{plural} ago"

    @classmethod
    def now(cls, tz: str | Timezone | None = None) -> DateTime:
        if tz is None:
            tz = UTC
        if isinstance(tz, str):
            tz = get_timezone(tz)

        dt = dt.datetime.now(tz)
        return cls(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            tzinfo=dt.tzinfo,
        )