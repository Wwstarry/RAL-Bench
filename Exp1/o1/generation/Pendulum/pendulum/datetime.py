import datetime as _datetime
from .timezone import timezone
from .duration import Duration
from .formatting import diff_for_humans
from .utils import parse_iso8601

class DateTime(_datetime.datetime):
    def in_timezone(self, tz):
        if isinstance(tz, str):
            tz = timezone(tz)
        return self.astimezone(tz)

    def add(self, duration):
        if not isinstance(duration, Duration):
            raise TypeError("duration must be a Duration")
        delta = duration.as_timedelta()
        return self + delta

    def diff_for_humans(self, other=None):
        return diff_for_humans(self, other)

    def __sub__(self, other):
        if isinstance(other, DateTime):
            diff = super().__sub__(other)
            return Duration(microseconds=int(diff.total_seconds() * 1_000_000))
        return super().__sub__(other)

def datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0, tz=None):
    if tz is not None:
        if isinstance(tz, str):
            tz = timezone(tz)
        return DateTime(year, month, day, hour, minute, second, microsecond, tzinfo=tz)
    else:
        return DateTime(year, month, day, hour, minute, second, microsecond)

def parse(dt_str, tz=None, strict=False):
    dt = parse_iso8601(dt_str)
    d = DateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, dt.tzinfo)
    if tz is not None:
        if isinstance(tz, str):
            tz = timezone(tz)
        d = d.in_timezone(tz)
    return d