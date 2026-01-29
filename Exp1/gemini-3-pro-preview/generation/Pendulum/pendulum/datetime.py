import datetime as _dt
import math
from .timezone import Timezone, fixed_timezone
from .duration import Duration
from .utils import add_months
from .formatting import diff_for_humans, to_iso8601_string

class DateTime(_dt.datetime):
    """
    Active DateTime class for Pendulum.
    """

    def __new__(cls, year, month, day, hour=0, minute=0, second=0, microsecond=0, tz=None):
        if tz is not None:
            if isinstance(tz, str):
                tz = Timezone(tz)
        else:
            tz = Timezone("UTC")
            
        return super().__new__(cls, year, month, day, hour, minute, second, microsecond, tzinfo=tz)

    @classmethod
    def create(cls, year, month, day, hour=0, minute=0, second=0, microsecond=0, tz=None):
        return cls(year, month, day, hour, minute, second, microsecond, tz)

    @classmethod
    def now(cls, tz=None):
        if tz is None:
            tz = Timezone("UTC")
        elif isinstance(tz, str):
            tz = Timezone(tz)
        
        dt = _dt.datetime.now(tz)
        return cls(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, tz=dt.tzinfo)

    @classmethod
    def utcnow(cls):
        return cls.now("UTC")

    @classmethod
    def today(cls):
        return cls.now()

    def in_timezone(self, tz):
        """
        Convert the DateTime to a new timezone.
        """
        if isinstance(tz, str):
            tz = Timezone(tz)
        
        dt = self.astimezone(tz)
        return DateTime(
            dt.year, dt.month, dt.day,
            dt.hour, dt.minute, dt.second, dt.microsecond,
            tz=dt.tzinfo
        )
    
    def in_tz(self, tz):
        return self.in_timezone(tz)

    def add(self, years=0, months=0, weeks=0, days=0, hours=0, minutes=0, seconds=0, microseconds=0):
        """
        Add duration to the instance.
        """
        new_dt = self
        
        if years or months:
            total_months = months + (years * 12)
            new_dt = add_months(new_dt, total_months)
            
        delta = _dt.timedelta(
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            microseconds=microseconds
        )
        
        res = super(DateTime, new_dt).__add__(delta)
        return DateTime(
            res.year, res.month, res.day,
            res.hour, res.minute, res.second, res.microsecond,
            tz=res.tzinfo
        )

    def subtract(self, years=0, months=0, weeks=0, days=0, hours=0, minutes=0, seconds=0, microseconds=0):
        """
        Subtract duration from the instance.
        """
        return self.add(
            years=-years, months=-months, weeks=-weeks, days=-days,
            hours=-hours, minutes=-minutes, seconds=-seconds, microseconds=-microseconds
        )

    def diff_for_humans(self, other=None, absolute=False, locale=None):
        return diff_for_humans(self, other, absolute, locale)

    def to_iso8601_string(self):
        return to_iso8601_string(self)

    def to_date_string(self):
        return self.strftime('%Y-%m-%d')

    def to_time_string(self):
        return self.strftime('%H:%M:%S')

    def to_datetime_string(self):
        return self.strftime('%Y-%m-%d %H:%M:%S')

    def __add__(self, other):
        if isinstance(other, _dt.timedelta):
            res = super().__add__(other)
            return DateTime(
                res.year, res.month, res.day,
                res.hour, res.minute, res.second, res.microsecond,
                tz=res.tzinfo
            )
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, _dt.datetime):
            # Return Pendulum Duration
            delta = super().__sub__(other)
            return Duration(days=delta.days, seconds=delta.seconds, microseconds=delta.microseconds)
        elif isinstance(other, _dt.timedelta):
            res = super().__sub__(other)
            return DateTime(
                res.year, res.month, res.day,
                res.hour, res.minute, res.second, res.microsecond,
                tz=res.tzinfo
            )
        return NotImplemented

    @property
    def timezone_name(self):
        return self.tzinfo.key if hasattr(self.tzinfo, 'key') else str(self.tzinfo)

    @property
    def offset(self):
        return int(self.utcoffset().total_seconds())

    @property
    def float_timestamp(self):
        return self.timestamp()

    @property
    def int_timestamp(self):
        return int(self.timestamp())