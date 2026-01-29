from __future__ import annotations

import datetime as _dt


def _require_int(name: str, value):
    if not isinstance(value, int):
        raise TypeError(f"{name} must be int")


class Duration:
    __slots__ = (
        "_years",
        "_months",
        "_days",
        "_seconds",
        "_microseconds",
    )

    def __init__(
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
        for k, v in [
            ("years", years),
            ("months", months),
            ("weeks", weeks),
            ("days", days),
            ("hours", hours),
            ("minutes", minutes),
            ("seconds", seconds),
            ("microseconds", microseconds),
        ]:
            _require_int(k, v)

        days = days + weeks * 7

        total_micro = microseconds
        total_sec = seconds + minutes * 60 + hours * 3600

        # Normalize microseconds into seconds
        carry_sec, micro = divmod(total_micro, 1_000_000)
        total_sec += carry_sec

        # Normalize seconds into days
        carry_days, sec = divmod(total_sec, 86400)
        days += carry_days

        self._years = years
        self._months = months
        self._days = int(days)
        self._seconds = int(sec)
        self._microseconds = int(micro)

    @property
    def years(self) -> int:
        return self._years

    @property
    def months(self) -> int:
        return self._months

    @property
    def weeks(self) -> int:
        # Not stored separately; approximate using full weeks in day component.
        return self._days // 7

    @property
    def days(self) -> int:
        return self._days

    @property
    def hours(self) -> int:
        return self._seconds // 3600

    @property
    def minutes(self) -> int:
        return (self._seconds % 3600) // 60

    @property
    def seconds(self) -> int:
        return self._seconds % 60

    @property
    def microseconds(self) -> int:
        return self._microseconds

    def as_timedelta(self) -> _dt.timedelta:
        return _dt.timedelta(days=self._days, seconds=self._seconds, microseconds=self._microseconds)

    def total_seconds(self) -> float:
        # If years/months are non-zero, ignore them (no fixed duration).
        return self.as_timedelta().total_seconds()

    def __add__(self, other: "Duration") -> "Duration":
        if not isinstance(other, Duration):
            return NotImplemented
        return Duration(
            years=self._years + other._years,
            months=self._months + other._months,
            days=self._days + other._days,
            seconds=self._seconds + other._seconds,
            microseconds=self._microseconds + other._microseconds,
        )

    def __sub__(self, other: "Duration") -> "Duration":
        if not isinstance(other, Duration):
            return NotImplemented
        return Duration(
            years=self._years - other._years,
            months=self._months - other._months,
            days=self._days - other._days,
            seconds=self._seconds - other._seconds,
            microseconds=self._microseconds - other._microseconds,
        )

    def __neg__(self) -> "Duration":
        return Duration(
            years=-self._years,
            months=-self._months,
            days=-self._days,
            seconds=-self._seconds,
            microseconds=-self._microseconds,
        )

    def __abs__(self) -> "Duration":
        # For "fixed" portion, take abs of timedelta then keep y/m absolute too.
        td = abs(self.as_timedelta())
        return Duration(
            years=abs(self._years),
            months=abs(self._months),
            days=td.days,
            seconds=td.seconds,
            microseconds=td.microseconds,
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, Duration):
            return False
        return (
            self._years == other._years
            and self._months == other._months
            and self._days == other._days
            and self._seconds == other._seconds
            and self._microseconds == other._microseconds
        )

    def __lt__(self, other) -> bool:
        if not isinstance(other, Duration):
            return NotImplemented
        # Best-effort ordering: fixed part first, then years/months.
        a = (self.as_timedelta().total_seconds(), self._years, self._months)
        b = (other.as_timedelta().total_seconds(), other._years, other._months)
        return a < b

    def __repr__(self) -> str:
        return (
            "Duration("
            f"years={self._years}, months={self._months}, "
            f"days={self._days}, seconds={self._seconds}, microseconds={self._microseconds}"
            ")"
        )

    def in_words(self, locale: str | None = None, short: bool = False, parts: int = 1) -> str:
        # English-only; interpret the fixed timedelta magnitude for phrasing.
        seconds = abs(self.as_timedelta().total_seconds())
        if seconds < 1:
            return "just now" if not short else "now"

        units = [
            ("year", 365 * 86400, "y"),
            ("month", 30 * 86400, "mo"),
            ("week", 7 * 86400, "w"),
            ("day", 86400, "d"),
            ("hour", 3600, "h"),
            ("minute", 60, "m"),
            ("second", 1, "s"),
        ]

        remaining = int(seconds)
        chosen = []
        for name, size, abbr in units:
            if remaining <= 0:
                break
            if size == 0:
                continue
            qty = remaining // size
            if qty == 0 and not chosen:
                continue
            if qty:
                chosen.append((name, qty, abbr))
                remaining -= qty * size
            if len(chosen) >= max(1, parts):
                break

        if not chosen:
            chosen = [("second", 0, "s")]

        def fmt_one(nm: str, qty: int, ab: str) -> str:
            if short:
                return f"{qty}{ab}"
            if qty == 1:
                return f"1 {nm}"
            return f"{qty} {nm}s"

        return ", ".join(fmt_one(nm, qty, ab) for nm, qty, ab in chosen)