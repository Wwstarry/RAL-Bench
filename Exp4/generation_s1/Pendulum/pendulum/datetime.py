from __future__ import annotations

import datetime as _dt
from typing import Any, Optional, Union, overload

from .duration import Duration, duration as _duration
from .formatting import diff_for_humans_from_seconds
from .timezone import UTC, timezone as _timezone
from .utils import _add_months, _clamp_day, now as _now, parse_iso8601


class DateTime(_dt.datetime):
    @property
    def timezone(self) -> Optional[_dt.tzinfo]:
        return self.tzinfo

    def in_timezone(self, tz: Optional[Union[str, int, _dt.tzinfo]]) -> "DateTime":
        tzinfo = _timezone(tz)
        if self.tzinfo is None:
            # deterministic: treat naive as wall time in target tz (no shift)
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
        return DateTime.from_datetime(self.astimezone(tzinfo))

    def add(
        self,
        *,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0,
    ) -> "DateTime":
        dt: _dt.datetime = self

        if years or months:
            total_months = years * 12 + months
            ny, nm = _add_months(dt.year, dt.month, total_months)
            nd = _clamp_day(ny, nm, dt.day)
            dt = dt.replace(year=ny, month=nm, day=nd)

        if any((weeks, days, hours, minutes, seconds, microseconds)):
            dt = dt + _dt.timedelta(
                weeks=weeks,
                days=days,
                hours=hours,
                minutes=minutes,
                seconds=seconds,
                microseconds=microseconds,
            )

        return DateTime.from_datetime(dt)

    def subtract(self, **kwargs: Any) -> "DateTime":
        neg = {k: -int(v) for k, v in kwargs.items()}
        return self.add(**neg)

    def diff_for_humans(
        self,
        other: Optional[Union[_dt.datetime, "DateTime"]] = None,
        *,
        absolute: bool = False,
        locale: str = "en",
        suffix: bool = True,
    ) -> str:
        # locale is accepted for compatibility; only "en" supported here
        if other is None:
            if self.tzinfo is None:
                other_dt = _now()
            else:
                other_dt = _now(self.tzinfo)
        else:
            other_dt = other

        # Compare as instants if both aware, else naive arithmetic
        delta = self - other_dt  # uses our __sub__ returning Duration for datetime; but other_dt may be datetime
        if isinstance(delta, Duration):
            secs = delta.as_timedelta().total_seconds()
        else:
            secs = delta.total_seconds()
        return diff_for_humans_from_seconds(secs, absolute=absolute, suffix=suffix)

    @classmethod
    def from_datetime(cls, dt: _dt.datetime) -> "DateTime":
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

    def __add__(self, other: Any):
        if isinstance(other, Duration):
            result = self
            if other.years or other.months:
                result = result.add(years=other.years, months=other.months)
            td = other.as_timedelta()
            return DateTime.from_datetime(_dt.datetime.__add__(result, td))
        if isinstance(other, _dt.timedelta):
            return DateTime.from_datetime(_dt.datetime.__add__(self, other))
        return NotImplemented

    def __radd__(self, other: Any):
        if isinstance(other, _dt.timedelta):
            return DateTime.from_datetime(_dt.datetime.__add__(self, other))
        if isinstance(other, Duration):
            return self.__add__(other)
        return NotImplemented

    def __sub__(self, other: Any):
        if isinstance(other, Duration):
            return self + (-other)
        if isinstance(other, _dt.timedelta):
            return DateTime.from_datetime(_dt.datetime.__sub__(self, other))
        if isinstance(other, _dt.datetime):
            td = _dt.datetime.__sub__(self, other)
            return Duration(
                years=0,
                months=0,
                weeks=0,
                days=td.days,
                seconds=td.seconds,
                microseconds=td.microseconds,
            )
        return NotImplemented


def datetime(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    microsecond: int = 0,
    tz: Optional[Union[str, int, _dt.tzinfo]] = None,
    fold: int = 0,
) -> DateTime:
    tzinfo = None if tz is None else _timezone(tz)
    return DateTime(
        year,
        month,
        day,
        hour,
        minute,
        second,
        microsecond,
        tzinfo=tzinfo,
        fold=fold,
    )


def parse(text: str, tz: Optional[Union[str, int, _dt.tzinfo]] = None, strict: bool = False) -> DateTime:
    parts = parse_iso8601(text, strict=strict)
    tzinfo_param = None if tz is None else _timezone(tz)

    year = parts["year"]
    month = parts["month"]
    day = parts["day"]
    hour = parts["hour"]
    minute = parts["minute"]
    second = parts["second"]
    micro = parts["microsecond"]
    tz_text = parts["tz"]

    if tz_text in (None, ""):
        # no tz info in string
        if tzinfo_param is None:
            return datetime(year, month, day, hour, minute, second, micro, tz=None)
        # interpret as local time in provided tz (attach, no conversion)
        return datetime(year, month, day, hour, minute, second, micro, tz=tzinfo_param)

    # tz info exists in string
    if tz_text in ("Z", "UTC"):
        base_tz = UTC
    else:
        base_tz = _timezone(tz_text)

    dt = datetime(year, month, day, hour, minute, second, micro, tz=base_tz)

    if tzinfo_param is not None:
        return dt.in_timezone(tzinfo_param)
    return dt