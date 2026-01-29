"""
Light-weight drop-in subset of `dateutil.relativedelta.relativedelta`.

Only the functionality needed by the test-suite is provided.  In particular we
support:

    * Construction via keyword arguments (years, months, weeks, days, hours,
      minutes, seconds, microseconds) or by passing two date/time objects to
      compute their difference.
    * Arithmetic with :class:`datetime.date` and :class:`datetime.datetime`
      objects using ``+`` or ``-``.
"""
from __future__ import annotations

import calendar as _cal
import datetime as _dt
from typing import Any, Optional


def _last_day_of_month(year: int, month: int) -> int:
    return _cal.monthrange(year, month)[1]


class relativedelta:
    __slots__ = (
        "years",
        "months",
        "days",
        "hours",
        "minutes",
        "seconds",
        "microseconds",
    )

    # ---------------------------------------------------------------------
    # Construction helpers
    # ---------------------------------------------------------------------
    def __init__(
        self,
        dt1: Optional[_dt.datetime | _dt.date] = None,
        dt2: Optional[_dt.datetime | _dt.date] = None,
        *,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0,
    ):
        if dt1 is not None and dt2 is not None:
            if isinstance(dt1, _dt.date) and isinstance(dt2, _dt.date):
                self._init_from_dates(dt1, dt2)
                return
            else:
                raise TypeError("dt1 and dt2 must both be date or datetime")
        self.years = years
        self.months = months
        # Convert weeks into days
        self.days = days + weeks * 7
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.microseconds = microseconds

    def _init_from_dates(self, dt1: _dt.date, dt2: _dt.date) -> None:
        if isinstance(dt1, _dt.datetime):
            dt1 = dt1.replace(tzinfo=None)
        if isinstance(dt2, _dt.datetime):
            dt2 = dt2.replace(tzinfo=None)

        sign = 1
        if dt2 < dt1:
            dt1, dt2 = dt2, dt1
            sign = -1

        # Years / months difference
        yrs = dt2.year - dt1.year
        mths = dt2.month - dt1.month
        days = dt2.day - dt1.day

        if days < 0:
            mths -= 1
            prev_month = (dt2.month - 1) or 12
            prev_year = dt2.year - (1 if dt2.month == 1 else 0)
            days += _last_day_of_month(prev_year, prev_month)

        if mths < 0:
            yrs -= 1
            mths += 12

        self.years = yrs * sign
        self.months = mths * sign
        self.days = days * sign
        self.hours = self.minutes = self.seconds = self.microseconds = 0

    # ---------------------------------------------------------------------
    # Arithmetic
    # ---------------------------------------------------------------------
    def _apply(self, dt: _dt.datetime | _dt.date, factor: int = 1):
        if isinstance(dt, _dt.datetime):
            date_part = dt.date()
            time_part = _dt.timedelta(
                hours=dt.hour,
                minutes=dt.minute,
                seconds=dt.second,
                microseconds=dt.microsecond,
            )
            tzinfo = dt.tzinfo
        else:
            date_part = dt
            time_part = _dt.timedelta(0)
            tzinfo = None

        # Years and months
        year = date_part.year + factor * self.years
        month = date_part.month + factor * self.months
        if month > 12 or month < 1:
            # Normalize months/years
            year_delta, month = divmod(month - 1, 12)
            month += 1
            year += year_delta

        day = min(date_part.day, _last_day_of_month(year, month))
        new_date = _dt.date(year, month, day)

        # Days + time delta
        delta = _dt.timedelta(
            days=factor * self.days,
            hours=factor * self.hours,
            minutes=factor * self.minutes,
            seconds=factor * self.seconds,
            microseconds=factor * self.microseconds,
        )
        new_datetime = _dt.datetime.combine(new_date, _dt.time()) + time_part + delta

        if tzinfo is not None:
            new_datetime = new_datetime.replace(tzinfo=tzinfo)

        if isinstance(dt, _dt.date) and not isinstance(dt, _dt.datetime):
            return new_datetime.date()
        return new_datetime

    # Public arithmetic operators
    def __add__(self, other: Any):
        if isinstance(other, (_dt.date, _dt.datetime)):
            return self._apply(other, 1)
        raise TypeError(f"Unsupported addition between relativedelta and {type(other)}")

    def __radd__(self, other: Any):
        return self.__add__(other)

    def __sub__(self, other: Any):
        if isinstance(other, (_dt.date, _dt.datetime)):
            return self._apply(other, -1)
        if isinstance(other, relativedelta):
            return relativedelta(
                years=self.years - other.years,
                months=self.months - other.months,
                days=self.days - other.days,
                hours=self.hours - other.hours,
                minutes=self.minutes - other.minutes,
                seconds=self.seconds - other.seconds,
                microseconds=self.microseconds - other.microseconds,
            )
        raise TypeError("Unsupported subtraction")

    def __rsub__(self, other: Any):
        if isinstance(other, (_dt.date, _dt.datetime)):
            return self._apply(other, -1)
        raise TypeError("Unsupported subtraction")

    def __neg__(self):
        return relativedelta(
            years=-self.years,
            months=-self.months,
            days=-self.days,
            hours=-self.hours,
            minutes=-self.minutes,
            seconds=-self.seconds,
            microseconds=-self.microseconds,
        )

    # String representation (for debugging)
    def __repr__(self):
        parts = []
        for attr in (
            "years",
            "months",
            "days",
            "hours",
            "minutes",
            "seconds",
            "microseconds",
        ):
            val = getattr(self, attr)
            if val:
                parts.append(f"{attr}={val}")
        return f"relativedelta({', '.join(parts)})" if parts else "relativedelta()"