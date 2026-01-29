import re
from datetime import timedelta as _timedelta, tzinfo as _tzinfo, datetime as _datetime
from .timezone import Timezone, timezone
from .duration import Duration
from .utils import _parse_iso8601_datetime


class DateTime:
    __slots__ = ("_dt",)

    def __init__(self, year, month=1, day=1, hour=0, minute=0, second=0, microsecond=0, tz=None):
        if tz is None:
            tz = timezone("UTC")
        elif not isinstance(tz, Timezone):
            raise TypeError("tz must be a pendulum.timezone.Timezone instance or None")
        self._dt = _datetime(year, month, day, hour, minute, second, microsecond, tzinfo=tz)

    @classmethod
    def from_datetime(cls, dt):
        # dt is a standard datetime.datetime instance
        if dt.tzinfo is None:
            tz = timezone("UTC")
            dt = dt.replace(tzinfo=tz)
        else:
            # Wrap tzinfo in Timezone if possible
            if isinstance(dt.tzinfo, Timezone):
                tz = dt.tzinfo
            else:
                # fallback: create a fixed offset timezone from dt.tzinfo.utcoffset()
                offset = dt.tzinfo.utcoffset(dt)
                if offset is None:
                    tz = timezone("UTC")
                else:
                    total_seconds = int(offset.total_seconds())
                    sign = "+" if total_seconds >= 0 else "-"
                    hh = abs(total_seconds) // 3600
                    mm = (abs(total_seconds) % 3600) // 60
                    tzname = f"UTC{sign}{hh:02d}:{mm:02d}"
                    tz = timezone(tzname)
            dt = dt.replace(tzinfo=tz)
        obj = cls.__new__(cls)
        obj._dt = dt
        return obj

    @classmethod
    def now(cls, tz=None):
        if tz is None:
            tz = timezone("UTC")
        elif not isinstance(tz, Timezone):
            raise TypeError("tz must be a pendulum.timezone.Timezone instance or None")
        dt = _datetime.now(tz)
        return cls.from_datetime(dt)

    @classmethod
    def utcnow(cls):
        dt = _datetime.utcnow().replace(tzinfo=timezone("UTC"))
        return cls.from_datetime(dt)

    @classmethod
    def datetime(cls, year, month=1, day=1, hour=0, minute=0, second=0, microsecond=0, tz=None):
        return cls(year, month, day, hour, minute, second, microsecond, tz)

    def __repr__(self):
        return f"<DateTime [{self.to_iso8601_string()}]>"

    def __str__(self):
        return self.to_iso8601_string()

    def __eq__(self, other):
        if not isinstance(other, DateTime):
            return False
        return self._dt == other._dt

    def __sub__(self, other):
        if isinstance(other, DateTime):
            delta = self._dt - other._dt
            return Duration.from_timedelta(delta)
        raise TypeError("Subtraction only supported between DateTime instances")

    def add(self, years=0, months=0, days=0, hours=0, minutes=0, seconds=0, microseconds=0):
        # Adding years and months is tricky because months have variable length
        # We'll do a naive approach: add years and months to year/month, then days/hours/minutes/seconds/microseconds to datetime
        y = self._dt.year + years
        m = self._dt.month + months
        # Normalize month overflow
        while m > 12:
            y += 1
            m -= 12
        while m < 1:
            y -= 1
            m += 12

        # Clamp day to max day in target month
        d = min(self._dt.day, _days_in_month(y, m))

        # Create new datetime with adjusted year, month, day
        new_dt = self._dt.replace(year=y, month=m, day=d)

        # Add days, hours, minutes, seconds, microseconds via timedelta
        delta = _timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)
        new_dt = new_dt + delta

        return DateTime.from_datetime(new_dt)

    def in_timezone(self, tz):
        if not isinstance(tz, Timezone):
            raise TypeError("tz must be a pendulum.timezone.Timezone instance")
        dt = self._dt.astimezone(tz)
        return DateTime.from_datetime(dt)

    def to_iso8601_string(self):
        # Format ISO8601 with timezone offset
        dt = self._dt
        s = dt.strftime("%Y-%m-%dT%H:%M:%S")
        if dt.microsecond:
            s += f".{dt.microsecond:06d}"
        offset = dt.utcoffset()
        if offset is None or offset.total_seconds() == 0:
            s += "Z"
        else:
            total_seconds = int(offset.total_seconds())
            sign = "+" if total_seconds >= 0 else "-"
            total_seconds = abs(total_seconds)
            hh = total_seconds // 3600
            mm = (total_seconds % 3600) // 60
            s += f"{sign}{hh:02d}:{mm:02d}"
        return s

    def diff_for_humans(self, other=None, absolute=False):
        # Returns a human readable difference string between self and other
        # If other is None, compare to now in self's timezone
        if other is None:
            other = DateTime.now(self._dt.tzinfo)
        if not isinstance(other, DateTime):
            raise TypeError("other must be a DateTime instance or None")

        delta = self._dt - other._dt
        past = delta.total_seconds() < 0
        delta_seconds = abs(int(delta.total_seconds()))

        if delta_seconds < 10:
            diff = "just now"
        elif delta_seconds < 60:
            diff = f"{delta_seconds} seconds"
        elif delta_seconds < 3600:
            minutes = delta_seconds // 60
            diff = f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif delta_seconds < 86400:
            hours = delta_seconds // 3600
            diff = f"{hours} hour{'s' if hours != 1 else ''}"
        elif delta_seconds < 2592000:
            days = delta_seconds // 86400
            diff = f"{days} day{'s' if days != 1 else ''}"
        elif delta_seconds < 31104000:
            months = delta_seconds // 2592000
            diff = f"{months} month{'s' if months != 1 else ''}"
        else:
            years = delta_seconds // 31104000
            diff = f"{years} year{'s' if years != 1 else ''}"

        if absolute or diff == "just now":
            return diff
        else:
            return f"{diff} ago" if past else f"in {diff}"


def datetime(year, month=1, day=1, hour=0, minute=0, second=0, microsecond=0, tz=None):
    return DateTime.datetime(year, month, day, hour, minute, second, microsecond, tz)


def parse(dt_str, tz=None):
    # Parse ISO8601 string to DateTime
    dt, parsed_tz = _parse_iso8601_datetime(dt_str)
    if tz is not None:
        if not isinstance(tz, Timezone):
            raise TypeError("tz must be a pendulum.timezone.Timezone instance or None")
        dt = dt.replace(tzinfo=tz)
    elif parsed_tz is None:
        dt = dt.replace(tzinfo=timezone("UTC"))
    else:
        dt = dt.replace(tzinfo=parsed_tz)
    return DateTime.from_datetime(dt)


def _days_in_month(year, month):
    # Return number of days in month for given year/month
    if month == 2:
        if _is_leap_year(year):
            return 29
        else:
            return 28
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31
    return 30


def _is_leap_year(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)