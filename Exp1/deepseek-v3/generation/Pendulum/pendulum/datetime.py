import datetime as dt
from .timezone import Timezone, FixedTimezone
from .duration import Duration
from .formatting import diff_for_humans
import pytz
import re

class DateTime(dt.datetime):

    @classmethod
    def now(cls, tz=None):
        if tz is None:
            return cls._from_datetime(dt.datetime.now())
        return cls._from_datetime(dt.datetime.now(tz))

    @classmethod
    def utcnow(cls):
        return cls._from_datetime(dt.datetime.utcnow()).replace(tzinfo=Timezone('UTC'))

    @classmethod
    def _from_datetime(cls, datetime):
        return cls(
            datetime.year, datetime.month, datetime.day,
            datetime.hour, datetime.minute, datetime.second,
            datetime.microsecond, datetime.tzinfo
        )

    @classmethod
    def parse(cls, text, tz=None):
        try:
            dt_naive = dt.datetime.strptime(text, '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
            try:
                dt_naive = dt.datetime.strptime(text, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                dt_naive = dt.datetime.strptime(text, '%Y-%m-%d')

        if tz is not None:
            return cls(
                dt_naive.year, dt_naive.month, dt_naive.day,
                dt_naive.hour, dt_naive.minute, dt_naive.second,
                dt_naive.microsecond, tz=tz
            )
        return cls._from_datetime(dt_naive)

    def __new__(cls, year, month, day, hour=0, minute=0, second=0, microsecond=0, tz=None):
        if tz is not None:
            if isinstance(tz, str):
                tz = Timezone(tz)
            elif not isinstance(tz, (Timezone, FixedTimezone)):
                raise ValueError('tz argument must be a timezone instance or string')

        self = super().__new__(
            cls, year, month, day, hour, minute, second, microsecond, tz
        )
        return self

    def in_timezone(self, tz):
        if isinstance(tz, str):
            tz = Timezone(tz)
        return self.astimezone(tz)

    def add(self, **kwargs):
        return self + Duration(**kwargs)

    def subtract(self, **kwargs):
        return self - Duration(**kwargs)

    def diff_for_humans(self, other=None, absolute=False):
        return diff_for_humans(self, other, absolute)

    def __add__(self, other):
        if isinstance(other, Duration):
            return self._from_datetime(super().__add__(other))
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, DateTime):
            return Duration(seconds=super().__sub__(other).total_seconds())
        elif isinstance(other, Duration):
            return self._from_datetime(super().__sub__(other))
        return NotImplemented