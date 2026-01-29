"""
DateTime class implementation.
"""

import datetime as dt
from pendulum.timezone import Timezone, timezone as get_timezone
from pendulum.duration import Duration
from pendulum.formatting import diff_for_humans


class DateTime(dt.datetime):
    """
    A DateTime class that extends the standard datetime with timezone support
    and additional utility methods.
    """

    def __new__(
        cls,
        year,
        month,
        day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tz=None,
        fold=0,
    ):
        """
        Create a new DateTime instance.
        """
        # Handle timezone
        if tz is None:
            tzinfo = dt.timezone.utc
        elif isinstance(tz, str):
            tzinfo = get_timezone(tz)
        elif isinstance(tz, Timezone):
            tzinfo = tz
        elif isinstance(tz, dt.tzinfo):
            tzinfo = tz
        else:
            tzinfo = dt.timezone.utc

        # Create the datetime object
        instance = dt.datetime.__new__(
            cls, year, month, day, hour, minute, second, microsecond, tzinfo, fold=fold
        )
        
        return instance

    @classmethod
    def now(cls, tz=None):
        """
        Get the current date and time.
        """
        if tz is None:
            tzinfo = dt.timezone.utc
        elif isinstance(tz, str):
            tzinfo = get_timezone(tz)
        elif isinstance(tz, Timezone):
            tzinfo = tz
        elif isinstance(tz, dt.tzinfo):
            tzinfo = tz
        else:
            tzinfo = dt.timezone.utc

        now = dt.datetime.now(tzinfo)
        return cls(
            now.year,
            now.month,
            now.day,
            now.hour,
            now.minute,
            now.second,
            now.microsecond,
            tz=tzinfo,
        )

    @classmethod
    def today(cls, tz=None):
        """
        Get today's date at midnight.
        """
        now = cls.now(tz=tz)
        return cls(now.year, now.month, now.day, 0, 0, 0, 0, tz=tz)

    @classmethod
    def yesterday(cls, tz=None):
        """
        Get yesterday's date at midnight.
        """
        today = cls.today(tz=tz)
        yesterday = today - dt.timedelta(days=1)
        return cls(
            yesterday.year,
            yesterday.month,
            yesterday.day,
            0,
            0,
            0,
            0,
            tz=tz,
        )

    @classmethod
    def tomorrow(cls, tz=None):
        """
        Get tomorrow's date at midnight.
        """
        today = cls.today(tz=tz)
        tomorrow = today + dt.timedelta(days=1)
        return cls(
            tomorrow.year,
            tomorrow.month,
            tomorrow.day,
            0,
            0,
            0,
            0,
            tz=tz,
        )

    def in_timezone(self, tz):
        """
        Convert this DateTime to a different timezone.
        
        Args:
            tz: Target timezone (string, Timezone object, or tzinfo)
        
        Returns:
            DateTime: A new DateTime instance in the target timezone
        """
        if isinstance(tz, str):
            tzinfo = get_timezone(tz)
        elif isinstance(tz, Timezone):
            tzinfo = tz
        elif isinstance(tz, dt.tzinfo):
            tzinfo = tz
        else:
            tzinfo = dt.timezone.utc

        # Convert to the new timezone
        converted = self.astimezone(tzinfo)
        
        return DateTime(
            converted.year,
            converted.month,
            converted.day,
            converted.hour,
            converted.minute,
            converted.second,
            converted.microsecond,
            tz=tzinfo,
        )

    def in_tz(self, tz):
        """
        Alias for in_timezone.
        """
        return self.in_timezone(tz)

    def add(
        self,
        years=0,
        months=0,
        weeks=0,
        days=0,
        hours=0,
        minutes=0,
        seconds=0,
        microseconds=0,
    ):
        """
        Add a duration to this DateTime.
        
        Args:
            years: Number of years to add
            months: Number of months to add
            weeks: Number of weeks to add
            days: Number of days to add
            hours: Number of hours to add
            minutes: Number of minutes to add
            seconds: Number of seconds to add
            microseconds: Number of microseconds to add
        
        Returns:
            DateTime: A new DateTime instance with the duration added
        """
        # Handle years and months separately
        year = self.year + years
        month = self.month + months
        
        # Normalize months
        while month > 12:
            month -= 12
            year += 1
        while month < 1:
            month += 12
            year -= 1
        
        # Handle day overflow
        day = self.day
        max_day = _days_in_month(year, month)
        if day > max_day:
            day = max_day
        
        # Create new datetime with adjusted year/month/day
        result = dt.datetime(
            year,
            month,
            day,
            self.hour,
            self.minute,
            self.second,
            self.microsecond,
            tzinfo=self.tzinfo,
        )
        
        # Add the timedelta components
        delta = dt.timedelta(
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            microseconds=microseconds,
        )
        result = result + delta
        
        return DateTime(
            result.year,
            result.month,
            result.day,
            result.hour,
            result.minute,
            result.second,
            result.microsecond,
            tz=result.tzinfo,
        )

    def subtract(
        self,
        years=0,
        months=0,
        weeks=0,
        days=0,
        hours=0,
        minutes=0,
        seconds=0,
        microseconds=0,
    ):
        """
        Subtract a duration from this DateTime.
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

    def __sub__(self, other):
        """
        Subtract another DateTime or timedelta from this DateTime.
        """
        if isinstance(other, (DateTime, dt.datetime)):
            # Return a Duration
            delta = dt.datetime.__sub__(self, other)
            return Duration(
                days=delta.days,
                seconds=delta.seconds,
                microseconds=delta.microseconds,
            )
        elif isinstance(other, (dt.timedelta, Duration)):
            # Return a DateTime
            result = dt.datetime.__sub__(self, other)
            return DateTime(
                result.year,
                result.month,
                result.day,
                result.hour,
                result.minute,
                result.second,
                result.microsecond,
                tz=result.tzinfo,
            )
        else:
            return NotImplemented

    def __add__(self, other):
        """
        Add a timedelta or Duration to this DateTime.
        """
        if isinstance(other, (dt.timedelta, Duration)):
            result = dt.datetime.__add__(self, other)
            return DateTime(
                result.year,
                result.month,
                result.day,
                result.hour,
                result.minute,
                result.second,
                result.microsecond,
                tz=result.tzinfo,
            )
        else:
            return NotImplemented

    def __radd__(self, other):
        """
        Right-hand addition.
        """
        return self.__add__(other)

    def diff(self, other=None, abs=True):
        """
        Get the difference between this DateTime and another.
        
        Args:
            other: Another DateTime (defaults to now)
            abs: Whether to return absolute value
        
        Returns:
            Duration: The difference as a Duration
        """
        if other is None:
            other = DateTime.now(tz=self.tzinfo)
        
        if not isinstance(other, (DateTime, dt.datetime)):
            raise TypeError("diff() argument must be a DateTime or datetime")
        
        delta = self - other
        
        if abs and delta.total_seconds() < 0:
            delta = other - self
        
        return delta

    def diff_for_humans(self, other=None, absolute=False, locale=None):
        """
        Get a human-readable difference string.
        
        Args:
            other: Another DateTime (defaults to now)
            absolute: Whether to omit the relative part (ago/from now)
            locale: Locale for formatting (not implemented)
        
        Returns:
            str: Human-readable difference
        """
        if other is None:
            other = DateTime.now(tz=self.tzinfo)
        
        return diff_for_humans(self, other, absolute=absolute)

    @property
    def timezone(self):
        """
        Get the timezone of this DateTime.
        """
        return self.tzinfo

    @property
    def timezone_name(self):
        """
        Get the timezone name of this DateTime.
        """
        if self.tzinfo is None:
            return None
        if hasattr(self.tzinfo, 'zone'):
            return self.tzinfo.zone
        return self.tzinfo.tzname(self)

    @property
    def offset(self):
        """
        Get the UTC offset in seconds.
        """
        if self.tzinfo is None:
            return 0
        offset = self.utcoffset()
        if offset is None:
            return 0
        return int(offset.total_seconds())

    @property
    def offset_hours(self):
        """
        Get the UTC offset in hours.
        """
        return self.offset / 3600

    def timestamp(self):
        """
        Get the Unix timestamp.
        """
        return dt.datetime.timestamp(self)

    def int_timestamp(self):
        """
        Get the Unix timestamp as an integer.
        """
        return int(self.timestamp())

    def float_timestamp(self):
        """
        Get the Unix timestamp as a float.
        """
        return float(self.timestamp())


def _days_in_month(year, month):
    """
    Get the number of days in a given month.
    """
    if month == 2:
        # Check for leap year
        if year % 400 == 0 or (year % 4 == 0 and year % 100 != 0):
            return 29
        return 28
    elif month in (4, 6, 9, 11):
        return 30
    else:
        return 31