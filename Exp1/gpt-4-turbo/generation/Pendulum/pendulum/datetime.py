import re
from datetime import datetime as _dt, timedelta as _td
from .timezone import timezone as _timezone, Timezone
from .duration import Duration
from .formatting import isoformat, parse_iso8601
from .utils import is_naive, local_timezone

class DateTime:
    def __init__(self, year, month, day, hour=0, minute=0, second=0, microsecond=0, tz=None):
        self._dt = _dt(year, month, day, hour, minute, second, microsecond)
        if tz is None:
            self._tz = local_timezone()
        elif isinstance(tz, str):
            self._tz = _timezone(tz)
        elif isinstance(tz, Timezone):
            self._tz = tz
        else:
            raise ValueError("Invalid timezone argument")
        self._offset = self._tz.utcoffset(self._dt)
        self._dt = self._dt.replace(tzinfo=self._tz)

    @property
    def year(self):
        return self._dt.year

    @property
    def month(self):
        return self._dt.month

    @property
    def day(self):
        return self._dt.day

    @property
    def hour(self):
        return self._dt.hour

    @property
    def minute(self):
        return self._dt.minute

    @property
    def second(self):
        return self._dt.second

    @property
    def microsecond(self):
        return self._dt.microsecond

    @property
    def tzinfo(self):
        return self._tz

    def __repr__(self):
        return f"<DateTime {self.isoformat()}>"

    def isoformat(self):
        return isoformat(self._dt)

    def in_timezone(self, tz):
        if isinstance(tz, str):
            tz = _timezone(tz)
        dt_utc = self._dt.astimezone(_timezone("UTC"))
        dt_new = dt_utc.astimezone(tz)
        return DateTime(
            dt_new.year, dt_new.month, dt_new.day,
            dt_new.hour, dt_new.minute, dt_new.second, dt_new.microsecond,
            tz=tz
        )

    def add(self, years=0, months=0, days=0, hours=0, minutes=0, seconds=0, microseconds=0):
        # Only days, hours, minutes, seconds, microseconds are supported for arithmetic
        # Years and months are handled naively (not considering leap years/month ends)
        y, m, d = self.year + years, self.month + months, self.day + days
        h, mi, s, ms = self.hour + hours, self.minute + minutes, self.second + seconds, self.microsecond + microseconds

        # Handle month overflow
        while m > 12:
            y += 1
            m -= 12
        while m < 1:
            y -= 1
            m += 12

        try:
            base = _dt(y, m, d, h, mi, s, ms, tzinfo=self._tz)
        except ValueError:
            # Fallback for invalid dates (e.g. Feb 30)
            max_day = 28
            while True:
                try:
                    base = _dt(y, m, max_day, h, mi, s, ms, tzinfo=self._tz)
                    break
                except ValueError:
                    max_day -= 1
        return DateTime(base.year, base.month, base.day, base.hour, base.minute, base.second, base.microsecond, tz=self._tz)

    def __sub__(self, other):
        if not isinstance(other, DateTime):
            raise TypeError("Subtraction only supported between DateTime objects")
        delta = self._dt.astimezone(_timezone("UTC")) - other._dt.astimezone(_timezone("UTC"))
        return Duration(days=delta.days, seconds=delta.seconds, microseconds=delta.microseconds)

    def diff_for_humans(self, other=None, absolute=False):
        if other is None:
            other = DateTime.now(tz=self._tz)
        delta = self - other
        return delta.diff_for_humans(self, other, absolute=absolute)

    @classmethod
    def now(cls, tz=None):
        if tz is None:
            tz = local_timezone()
        elif isinstance(tz, str):
            tz = _timezone(tz)
        dt = _dt.now(tz)
        return cls(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, tz=tz)

    @classmethod
    def utcnow(cls):
        dt = _dt.utcnow()
        return cls(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, tz=_timezone("UTC"))

    @classmethod
    def from_datetime(cls, dt, tz=None):
        if tz is None:
            tz = dt.tzinfo or local_timezone()
        return cls(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, tz=tz)

def datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0, tz=None):
    return DateTime(year, month, day, hour, minute, second, microsecond, tz=tz)

def parse(dt_str, tz=None):
    # Try ISO-8601 first
    dt, parsed_tz = parse_iso8601(dt_str)
    if tz is None:
        tz = parsed_tz or local_timezone()
    return DateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, tz=tz)