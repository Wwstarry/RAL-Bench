from __future__ import annotations

import datetime as _dt
from datetime import tzinfo

from .duration import Duration
from .formatting import format_datetime, to_iso8601
from .timezone import timezone as _timezone
from .utils import add_months, add_years


def _require_int(name: str, value):
    if not isinstance(value, int):
        raise TypeError(f"{name} must be int")


class DateTime(_dt.datetime):
    @classmethod
    def instance(cls, dt: _dt.datetime) -> "DateTime":
        if isinstance(dt, DateTime):
            return dt
        if not isinstance(dt, _dt.datetime):
            raise TypeError("dt must be a datetime")
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

    def in_timezone(self, tz: str | tzinfo) -> "DateTime":
        if self.tzinfo is None or self.utcoffset() is None:
            raise ValueError("Cannot convert naive DateTime")
        tzinfo = _timezone(tz)
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

        dt: _dt.datetime = self

        if years:
            dt = add_years(dt, years)
        if months:
            dt = add_months(dt, months)

        if weeks or days or hours or minutes or seconds or microseconds:
            delta = _dt.timedelta(
                days=days + weeks * 7,
                hours=hours,
                minutes=minutes,
                seconds=seconds,
                microseconds=microseconds,
            )
            dt = dt + delta

        return DateTime.instance(dt)

    def subtract(self, **kwargs) -> "DateTime":
        negated = {k: (-v if isinstance(v, int) else v) for k, v in kwargs.items()}
        return self.add(**negated)

    def diff(self, other: _dt.datetime | "DateTime" | None = None, absolute: bool = False) -> Duration:
        if other is None:
            other_dt = DateTime.now(self.tzinfo) if self.tzinfo is not None else DateTime.now()  # type: ignore[arg-type]
        else:
            other_dt = DateTime.instance(other)

        td = self - other_dt  # uses __sub__ override returning Duration
        if absolute:
            return abs(td)
        return td

    def diff_for_humans(
        self,
        other: _dt.datetime | "DateTime" | None = None,
        absolute: bool = False,
        locale: str | None = None,
        unit: str | None = None,
        short: bool = False,
        parts: int = 1,
    ) -> str:
        if other is None:
            other_dt = DateTime.now(self.tzinfo) if self.tzinfo is not None else DateTime.now()  # type: ignore[arg-type]
        else:
            other_dt = DateTime.instance(other)

        delta = self - other_dt  # Duration
        future = delta.as_timedelta().total_seconds() > 0
        fixed = abs(delta.as_timedelta())

        # Determine unit
        forced = unit.lower() if unit else None
        seconds = fixed.total_seconds()

        if seconds < 1:
            base = "just now" if not short else "now"
            return base if absolute else base

        def render(qty: int, name: str) -> str:
            if short:
                abbr = {
                    "second": "s",
                    "minute": "m",
                    "hour": "h",
                    "day": "d",
                    "week": "w",
                    "month": "mo",
                    "year": "y",
                }[name]
                core = f"{qty}{abbr}"
            else:
                core = f"{qty} {name}" + ("" if qty == 1 else "s")
            if absolute:
                return core
            return f"in {core}" if future else f"{core} ago"

        # forced unit path
        if forced:
            sizes = {
                "second": 1,
                "minute": 60,
                "hour": 3600,
                "day": 86400,
                "week": 7 * 86400,
                "month": 30 * 86400,
                "year": 365 * 86400,
            }
            if forced not in sizes:
                raise ValueError("Invalid unit")
            qty = int(seconds // sizes[forced])
            if qty == 0:
                qty = 1
            return render(qty, forced)

        # automatic unit with optional parts
        units = [
            ("year", 365 * 86400),
            ("month", 30 * 86400),
            ("week", 7 * 86400),
            ("day", 86400),
            ("hour", 3600),
            ("minute", 60),
            ("second", 1),
        ]

        remaining = int(seconds)
        picked: list[tuple[str, int]] = []
        for name, size in units:
            if remaining <= 0:
                break
            qty = remaining // size
            if qty == 0 and not picked:
                continue
            if qty:
                picked.append((name, qty))
                remaining -= qty * size
            if len(picked) >= max(1, parts):
                break

        if not picked:
            picked = [("second", 1)]

        if parts <= 1:
            return render(picked[0][1], picked[0][0])

        if short:
            core = ", ".join(
                f"{qty}{ {'second':'s','minute':'m','hour':'h','day':'d','week':'w','month':'mo','year':'y'}[name] }".replace(" ", "")
                for name, qty in picked
            )
        else:
            core = ", ".join(f"{qty} {name}" + ("" if qty == 1 else "s") for name, qty in picked)

        if absolute:
            return core
        return f"in {core}" if future else f"{core} ago"

    def to_iso8601_string(self) -> str:
        return to_iso8601(self)

    def format(self, fmt: str) -> str:
        return format_datetime(self, fmt)

    # Operators
    def __sub__(self, other):
        if isinstance(other, _dt.timedelta):
            return DateTime.instance(super().__sub__(other))
        if isinstance(other, _dt.datetime):
            td = super().__sub__(other)
            return Duration(days=td.days, seconds=td.seconds, microseconds=td.microseconds)
        return NotImplemented

    def __add__(self, other):
        if isinstance(other, _dt.timedelta):
            return DateTime.instance(super().__add__(other))
        return NotImplemented