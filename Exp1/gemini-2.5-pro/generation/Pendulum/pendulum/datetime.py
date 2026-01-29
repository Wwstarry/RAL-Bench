# -*- coding: utf-8 -*-

import datetime as _dt
import calendar
from .utils import _get_tzinfo
from .duration import Duration
from .timezone import UTC

class DateTime(_dt.datetime):
    """
    An enhanced version of the standard datetime.datetime class.
    """

    def __new__(cls, year, month, day, hour=0, minute=0, second=0, microsecond=0, tz=None, fold=0):
        if tz is not None:
            tz = _get_tzinfo(tz)
        
        if not isinstance(fold, int):
            raise ValueError("fold must be an integer")

        dt = super().__new__(cls, year, month, day, hour, minute, second, microsecond, tzinfo=tz, fold=fold)
        return dt

    @classmethod
    def now(cls, tz=None):
        if tz is None:
            dt = _dt.datetime.now()
            return cls(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, tz=dt.tzinfo)
        
        tz = _get_tzinfo(tz)
        dt = _dt.datetime.now(tz)
        return cls(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, tz=tz)

    @classmethod
    def fromtimestamp(cls, timestamp, tz=None):
        if tz is None:
            tz = UTC
        tz = _get_tzinfo(tz)
        dt = super().fromtimestamp(timestamp, tz)
        return cls(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, tz=dt.tzinfo)

    def in_timezone(self, tz):
        """
        Convert the instance to a given timezone.
        """
        tz = _get_tzinfo(tz)
        dt = self.astimezone(tz)
        return self.__class__(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, tz=dt.tzinfo, fold=dt.fold)

    def add(self, **kwargs):
        """
        Adds a duration to the instance.
        """
        duration = Duration(**kwargs)
        return self._add_duration(duration)

    def subtract(self, **kwargs):
        """
        Removes a duration from the instance.
        """
        duration = Duration(**kwargs)
        return self._add_duration(-duration)

    def _add_duration(self, duration):
        """
        Adds a Duration instance.
        """
        new_dt = self

        # Add timedelta part first
        if duration.timedelta:
            new_dt = super(DateTime, new_dt).__add__(duration.timedelta)

        # Add years and months
        if duration.years or duration.months:
            year = new_dt.year + duration.years
            month = new_dt.month + duration.months

            # Normalize month and year
            year += (month - 1) // 12
            month = (month - 1) % 12 + 1

            # Handle day overflow
            day = min(new_dt.day, calendar.monthrange(year, month)[1])
            
            new_dt = new_dt.replace(year=year, month=month, day=day)

        return self.__class__(
            new_dt.year, new_dt.month, new_dt.day,
            new_dt.hour, new_dt.minute, new_dt.second, new_dt.microsecond,
            tz=new_dt.tzinfo, fold=new_dt.fold
        )

    def __add__(self, other):
        if isinstance(other, Duration):
            return self._add_duration(other)
        if isinstance(other, _dt.timedelta):
            dt = super().__add__(other)
            return self.__class__(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, tz=dt.tzinfo, fold=dt.fold)
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, _dt.datetime):
            # To be compatible with Pendulum, subtraction should return a Duration
            # that represents the interval, not just a simple timedelta.
            # This is a complex problem. We'll return a Duration wrapping a timedelta,
            # which is sufficient for diff_for_humans and basic arithmetic.
            if self.tzinfo != other.tzinfo:
                other = other.astimezone(self.tzinfo)
            
            delta = super().__sub__(other)
            return Duration(seconds=delta.total_seconds())

        if isinstance(other, Duration):
            return self._add_duration(-other)
        if isinstance(other, _dt.timedelta):
            dt = super().__sub__(other)
            return self.__class__(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, tz=dt.tzinfo, fold=dt.fold)
        return NotImplemented

    def start_of(self, unit):
        """
        Returns a new instance with the time set to the start of the given unit.
        """
        if unit == 'day':
            return self.replace(hour=0, minute=0, second=0, microsecond=0)
        # Other units can be implemented here
        raise ValueError(f"Unsupported unit '{unit}' for start_of")

    @classmethod
    def parse(cls, text, **options):
        """
        Parses a string representation of a date and time.
        """
        if not isinstance(text, str):
            raise TypeError("parse() argument must be a string")

        tz = options.get("tz")
        
        # Pre-process for fromisoformat compatibility
        # Replace first space with 'T'
        if 'T' not in text:
            parts = text.split(' ')
            if len(parts) > 1 and ':' in parts[1]:
                text = 'T'.join(parts)

        # Handle 'Z' for UTC
        has_z = text.upper().endswith('Z')
        if has_z:
            text = text[:-1] + "+00:00"

        try:
            dt = _dt.datetime.fromisoformat(text)
        except ValueError:
            raise ValueError(f"Unable to parse string '{text}'")

        if dt.tzinfo is None and tz:
            tz_info = _get_tzinfo(tz)
            dt = tz_info.localize(dt)
        
        return cls(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, tz=dt.tzinfo, fold=dt.fold)

    def diff_for_humans(self, other=None, absolute=False, locale=None):
        """
        Get the difference in a human-readable format.
        """
        from . import _formatter

        if other is None:
            other = self.now(self.tzinfo)

        is_now = other == self
        if is_now:
            return _formatter.format_diff(Duration(), is_now=True)

        diff = self - other
        
        return _formatter.format_diff(diff, absolute)