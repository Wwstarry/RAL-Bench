import datetime as _dt
from typing import Optional, Union

from .timezone import UTC
from .utils import days_in_month, ensure_timezone
from .duration import Duration
from .formatting import humanize_duration


class DateTime:
    """
    Minimal timezone-aware DateTime compatible with core Pendulum API patterns.

    Internally wraps a Python datetime.datetime (aware or naive).
    """

    __slots__ = ("_dt",)

    def __init__(
        self,
        year: int,
        month: int,
        day: int,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        microsecond: int = 0,
        tzinfo: Optional[_dt.tzinfo] = None,
    ):
        self._dt = _dt.datetime(year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)

    @classmethod
    def from_datetime(cls, dt: _dt.datetime) -> "DateTime":
        obj = cls.__new__(cls)
        obj._dt = dt
        return obj

    @classmethod
    def now(cls, tzinfo: Optional[_dt.tzinfo] = None) -> "DateTime":
        if tzinfo is None:
            return cls.from_datetime(_dt.datetime.now())
        return cls.from_datetime(_dt.datetime.now(tz=tzinfo))

    # Basic properties

    @property
    def tzinfo(self) -> Optional[_dt.tzinfo]:
        return self._dt.tzinfo

    @property
    def year(self) -> int:
        return self._dt.year

    @property
    def month(self) -> int:
        return self._dt.month

    @property
    def day(self) -> int:
        return self._dt.day

    @property
    def hour(self) -> int:
        return self._dt.hour

    @property
    def minute(self) -> int:
        return self._dt.minute

    @property
    def second(self) -> int:
        return self._dt.second

    @property
    def microsecond(self) -> int:
        return self._dt.microsecond

    def is_aware(self) -> bool:
        return self._dt.tzinfo is not None and self._dt.tzinfo.utcoffset(self._dt) is not None

    def to_datetime(self) -> _dt.datetime:
        return self._dt

    def timestamp(self) -> float:
        if self.is_aware():
            return self._dt.timestamp()
        # naive: assume system local mapping, but better convert as naive
        return self._dt.timestamp()

    # Representation

    def __repr__(self) -> str:
        return f"DateTime({self.isoformat()})"

    def __str__(self) -> str:
        return self.isoformat()

    def isoformat(self) -> str:
        """
        ISO 8601 string with timezone offset or 'Z' for UTC.
        """
        dt = self._dt
        s = dt.replace(tzinfo=None).isoformat()
        tz = dt.tzinfo
        if tz is None:
            return s
        offset = tz.utcoffset(dt)
        if offset is None:
            return s
        if offset == _dt.timedelta(0):
            # Use Z for UTC
            return s + "Z"
        # format offset as +HH:MM
        total_seconds = int(offset.total_seconds())
        sign = "+" if total_seconds >= 0 else "-"
        total_seconds = abs(total_seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{s}{sign}{hours:02d}:{minutes:02d}"

    def to_iso8601_string(self) -> str:
        return self.isoformat()

    # Timezone conversion

    def in_timezone(self, tz: Union[str, _dt.tzinfo]) -> "DateTime":
        tzinfo = ensure_timezone(tz)
        if tzinfo is None:
            # produce naive by converting to UTC then dropping tz? Here keep instant by converting to tzinfo None.
            return DateTime.from_datetime(self._dt.replace(tzinfo=None))
        if self.is_aware():
            new_dt = self._dt.astimezone(tzinfo)
        else:
            # naive assumed to be in tzinfo? We'll attach tzinfo without conversion.
            new_dt = self._dt.replace(tzinfo=tzinfo)
        return DateTime.from_datetime(new_dt)

    # Arithmetic

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
        """
        Calendar-aware addition for years/months and timedelta for others.
        """
        dt = self._dt

        # Handle month/year rollover
        y = dt.year + years
        m = dt.month + months

        if months or years:
            y += (m - 1) // 12
            m = ((m - 1) % 12) + 1

            d = min(dt.day, days_in_month(y, m))
            base = _dt.datetime(y, m, d, dt.hour, dt.minute, dt.second, dt.microsecond, tzinfo=dt.tzinfo)
        else:
            base = dt

        td = _dt.timedelta(days=days + weeks * 7, hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)
        new_dt = base + td
        return DateTime.from_datetime(new_dt)

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
    ) -> "DateTime":
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

    # Operators

    def __add__(self, other):
        if isinstance(other, Duration):
            return DateTime.from_datetime(self._dt + other._tdelta)
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, DateTime):
            a = self._dt
            b = other._dt
            if a.tzinfo is not None and b.tzinfo is not None:
                a_utc = a.astimezone(UTC)
                b_utc = b.astimezone(UTC)
                delta = a_utc - b_utc
            else:
                delta = a - b
            return Duration.from_timedelta(delta)
        if isinstance(other, Duration):
            return DateTime.from_datetime(self._dt - other._tdelta)
        return NotImplemented

    # Humanize

    def diff_for_humans(self, other: Optional["DateTime"] = None, absolute: bool = False) -> str:
        """
        Returns a human-readable difference string.

        Examples:
        - dt.diff_for_humans() -> 'in 2 hours' or '1 day ago'
        - dt1.diff_for_humans(dt2) -> '2 hours after' or '3 minutes before'
        """
        if other is None:
            ref = DateTime.now(self.tzinfo) if self.tzinfo is not None else DateTime.now()
            delta = self - ref
            seconds = delta.total_seconds()
            text = humanize_duration(seconds, absolute=absolute)
            if absolute:
                return text
            if seconds >= 0:
                return f"in {text}"
            else:
                return f"{text} ago"
        else:
            delta = self - other
            seconds = delta.total_seconds()
            text = humanize_duration(seconds, absolute=True)
            if absolute:
                return text
            if seconds >= 0:
                return f"{text} after"
            else:
                return f"{text} before"

    # Convenience

    def replace(self, **kwargs) -> "DateTime":
        """
        Return a new DateTime with replaced fields (like datetime.replace).
        Supported keys: year, month, day, hour, minute, second, microsecond, tzinfo
        """
        new_dt = self._dt.replace(**kwargs)
        return DateTime.from_datetime(new_dt)