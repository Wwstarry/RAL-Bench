# pendulum/duration.py
from __future__ import annotations

from datetime import timedelta


class Duration:
    """
    A class to represent a duration of time.
    """

    def __init__(
        self,
        days: float = 0,
        seconds: float = 0,
        microseconds: float = 0,
        milliseconds: float = 0,
        minutes: float = 0,
        hours: float = 0,
        weeks: float = 0,
        years: int = 0,
        months: int = 0,
    ) -> None:
        total_seconds = (
            seconds
            + minutes * 60
            + hours * 3600
        )
        total_days = days + weeks * 7
        total_microseconds = microseconds + milliseconds * 1000

        # Normalize seconds and microseconds
        d, s = divmod(total_seconds, 86400)
        total_days += d
        m, us = divmod(total_microseconds, 1000000)
        s += m
        d, s = divmod(s, 86400)
        total_days += d

        self._years = int(years)
        self._months = int(months)
        self._weeks = int(total_days / 7)
        self._days = int(total_days % 7)
        self._hours = int(s / 3600)
        self._minutes = int((s % 3600) / 60)
        self._seconds = int(s % 60)
        self._microseconds = int(us)

        # For timedelta compatibility
        self._td = timedelta(
            days=total_days, seconds=s, microseconds=self._microseconds
        )

    @property
    def years(self) -> int:
        return self._years

    @property
    def months(self) -> int:
        return self._months

    @property
    def weeks(self) -> int:
        return self._weeks

    @property
    def days(self) -> int:
        return self._days

    @property
    def hours(self) -> int:
        return self._hours

    @property
    def minutes(self) -> int:
        return self._minutes

    @property
    def seconds(self) -> int:
        return self._seconds

    @property
    def microseconds(self) -> int:
        return self._microseconds

    def in_words(self, locale: str = "en") -> str:
        """
        Returns the duration in a human-readable format.
        """
        parts = []
        if self.years:
            parts.append(f"{self.years} year{'s' if self.years > 1 else ''}")
        if self.months:
            parts.append(f"{self.months} month{'s' if self.months > 1 else ''}")
        if self.weeks:
            parts.append(f"{self.weeks} week{'s' if self.weeks > 1 else ''}")
        if self.days:
            parts.append(f"{self.days} day{'s' if self.days > 1 else ''}")
        if self.hours:
            parts.append(f"{self.hours} hour{'s' if self.hours > 1 else ''}")
        if self.minutes:
            parts.append(f"{self.minutes} minute{'s' if self.minutes > 1 else ''}")
        if self.seconds:
            parts.append(f"{self.seconds} second{'s' if self.seconds > 1 else ''}")

        return " ".join(parts)

    def total_seconds(self) -> float:
        # This is an approximation as years/months are not fixed durations.
        # It matches timedelta's behavior for the fixed parts.
        return self._td.total_seconds()

    def __repr__(self) -> str:
        return (
            f"<Duration years={self.years} months={self.months} weeks={self.weeks} "
            f"days={self.days} hours={self.hours} minutes={self.minutes} "
            f"seconds={self.seconds} microseconds={self.microseconds}>"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, Duration):
            return NotImplemented
        return self.total_seconds() == other.total_seconds() and self.years == other.years and self.months == other.months


def duration(**kwargs) -> Duration:
    """
    Creates a new Duration instance.
    """
    return Duration(**kwargs)