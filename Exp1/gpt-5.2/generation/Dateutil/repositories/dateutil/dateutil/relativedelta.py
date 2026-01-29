from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta


def _last_day_of_month(y: int, m: int) -> int:
    return calendar.monthrange(y, m)[1]


class relativedelta:
    """
    Calendar-aware relative delta.

    Supports years, months, days, hours, minutes, seconds, microseconds.
    Also supports adding to date/datetime and computing dt1 - dt2.
    """

    __slots__ = (
        "years",
        "months",
        "days",
        "hours",
        "minutes",
        "seconds",
        "microseconds",
    )

    def __init__(
        self,
        dt1=None,
        dt2=None,
        *,
        years=0,
        months=0,
        days=0,
        hours=0,
        minutes=0,
        seconds=0,
        microseconds=0,
    ):
        if dt1 is not None and dt2 is not None:
            if isinstance(dt1, (date, datetime)) and isinstance(dt2, (date, datetime)):
                self._from_dates(dt1, dt2)
                return
            raise TypeError("dt1 and dt2 must be date/datetime")

        self.years = int(years)
        self.months = int(months)
        self.days = int(days)
        self.hours = int(hours)
        self.minutes = int(minutes)
        self.seconds = int(seconds)
        self.microseconds = int(microseconds)

    def _from_dates(self, dt1, dt2):
        # Simplified but stable: compute years/months by calendar components, then remainder as timedelta
        if isinstance(dt1, date) and not isinstance(dt1, datetime):
            dt1 = datetime(dt1.year, dt1.month, dt1.day)
        if isinstance(dt2, date) and not isinstance(dt2, datetime):
            dt2 = datetime(dt2.year, dt2.month, dt2.day)

        sign = 1
        if dt1 < dt2:
            dt1, dt2 = dt2, dt1
            sign = -1

        y = dt1.year - dt2.year
        m = dt1.month - dt2.month
        if m < 0:
            y -= 1
            m += 12

        # Adjust if overshoot when applying y/m to dt2
        candidate = self._add_ym(dt2, y, m)
        if candidate > dt1:
            # back off one month
            m -= 1
            if m < 0:
                y -= 1
                m += 12
            candidate = self._add_ym(dt2, y, m)

        delta = dt1 - candidate
        self.years = sign * y
        self.months = sign * m
        self.days = sign * delta.days
        self.hours = sign * (delta.seconds // 3600)
        self.minutes = sign * ((delta.seconds % 3600) // 60)
        self.seconds = sign * (delta.seconds % 60)
        self.microseconds = sign * delta.microseconds

    @staticmethod
    def _add_ym(dt: datetime, years: int, months: int) -> datetime:
        y = dt.year + years
        m = dt.month + months
        y += (m - 1) // 12
        m = (m - 1) % 12 + 1
        d = min(dt.day, _last_day_of_month(y, m))
        return dt.replace(year=y, month=m, day=d)

    def __add__(self, other):
        if isinstance(other, (date, datetime)):
            return self._apply(other, 1)
        if isinstance(other, relativedelta):
            rd = relativedelta(
                years=self.years + other.years,
                months=self.months + other.months,
                days=self.days + other.days,
                hours=self.hours + other.hours,
                minutes=self.minutes + other.minutes,
                seconds=self.seconds + other.seconds,
                microseconds=self.microseconds + other.microseconds,
            )
            return rd
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, relativedelta):
            rd = relativedelta(
                years=self.years - other.years,
                months=self.months - other.months,
                days=self.days - other.days,
                hours=self.hours - other.hours,
                minutes=self.minutes - other.minutes,
                seconds=self.seconds - other.seconds,
                microseconds=self.microseconds - other.microseconds,
            )
            return rd
        return NotImplemented

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

    def _apply(self, dt, sign: int):
        is_date_only = isinstance(dt, date) and not isinstance(dt, datetime)
        if is_date_only:
            dt = datetime(dt.year, dt.month, dt.day)

        dt2 = self._add_ym(dt, sign * self.years, sign * self.months)
        td = timedelta(
            days=sign * self.days,
            hours=sign * self.hours,
            minutes=sign * self.minutes,
            seconds=sign * self.seconds,
            microseconds=sign * self.microseconds,
        )
        dt2 = dt2 + td

        if is_date_only:
            return dt2.date()
        return dt2

    def __repr__(self):
        parts = []
        for k in ("years", "months", "days", "hours", "minutes", "seconds", "microseconds"):
            v = getattr(self, k)
            if v:
                parts.append(f"{k}={v}")
        inside = ", ".join(parts) if parts else "0"
        return f"relativedelta({inside})"