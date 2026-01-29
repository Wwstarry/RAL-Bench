from datetime import datetime as dt, timedelta
from pendulum.timezone import timezone
from pendulum.duration import duration
import pendulum.formatting as formatting

class DateTime:
    def __init__(self, year, month, day, hour=0, minute=0, second=0, microsecond=0, tz=None):
        if isinstance(tz, str):
            tz = timezone(tz)
        self._dt = dt(year, month, day, hour, minute, second, microsecond, tzinfo=tz)

    @classmethod
    def now(cls, tz=None):
        if isinstance(tz, str):
            tz = timezone(tz)
        return cls.from_datetime(dt.now(tz))

    @classmethod
    def from_datetime(cls, datetime_obj):
        return cls(
            datetime_obj.year,
            datetime_obj.month,
            datetime_obj.day,
            datetime_obj.hour,
            datetime_obj.minute,
            datetime_obj.second,
            datetime_obj.microsecond,
            datetime_obj.tzinfo,
        )

    @classmethod
    def parse(cls, iso_string):
        parsed_dt = dt.fromisoformat(iso_string)
        return cls.from_datetime(parsed_dt)

    def in_timezone(self, tz):
        if isinstance(tz, str):
            tz = timezone(tz)
        new_dt = self._dt.astimezone(tz)
        return self.from_datetime(new_dt)

    def add(self, duration_obj):
        if not isinstance(duration_obj, timedelta):
            raise ValueError("Expected a timedelta object")
        new_dt = self._dt + duration_obj
        return self.from_datetime(new_dt)

    def subtract(self, other):
        if isinstance(other, DateTime):
            return self._dt - other._dt
        elif isinstance(other, timedelta):
            new_dt = self._dt - other
            return self.from_datetime(new_dt)
        else:
            raise ValueError("Unsupported type for subtraction")

    def diff_for_humans(self, other=None):
        if other is None:
            other = DateTime.now(self._dt.tzinfo)
        diff = self._dt - other._dt
        return formatting.humanize_duration(diff)

    def __str__(self):
        return self._dt.isoformat()

def datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0, tz=None):
    return DateTime(year, month, day, hour, minute, second, microsecond, tz)

def parse(iso_string):
    return DateTime.parse(iso_string)