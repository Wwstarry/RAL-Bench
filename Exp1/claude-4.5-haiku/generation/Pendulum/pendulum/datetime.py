import datetime as _datetime
from pendulum.timezone import Timezone
from pendulum.duration import Duration
from pendulum.formatting import format_datetime

class DateTime(_datetime.datetime):
    """A DateTime class that extends datetime.datetime with timezone and formatting support."""
    
    __slots__ = ()
    
    def __new__(cls, year, month=1, day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=None):
        if isinstance(tzinfo, str):
            tzinfo = Timezone(tzinfo)
        
        instance = _datetime.datetime.__new__(
            cls, year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo
        )
        return instance
    
    def in_timezone(self, tz):
        """Convert to another timezone."""
        if isinstance(tz, str):
            tz = Timezone(tz)
        
        if self.tzinfo is None:
            raise ValueError("Cannot convert naive datetime")
        
        converted = self.astimezone(tz)
        return DateTime(
            converted.year, converted.month, converted.day,
            converted.hour, converted.minute, converted.second, converted.microsecond,
            tzinfo=tz
        )
    
    def in_tz(self, tz):
        """Alias for in_timezone."""
        return self.in_timezone(tz)
    
    def add(self, **kwargs):
        """Add a duration to this datetime."""
        duration = Duration(**kwargs)
        result = self + duration
        return DateTime(
            result.year, result.month, result.day,
            result.hour, result.minute, result.second, result.microsecond,
            tzinfo=result.tzinfo
        )
    
    def subtract(self, **kwargs):
        """Subtract a duration from this datetime."""
        duration = Duration(**kwargs)
        result = self - duration
        return DateTime(
            result.year, result.month, result.day,
            result.hour, result.minute, result.second, result.microsecond,
            tzinfo=result.tzinfo
        )
    
    def __add__(self, other):
        if isinstance(other, Duration):
            result = _datetime.datetime.__add__(self, other.as_timedelta())
        else:
            result = _datetime.datetime.__add__(self, other)
        
        if isinstance(result, _datetime.datetime):
            return DateTime(
                result.year, result.month, result.day,
                result.hour, result.minute, result.second, result.microsecond,
                tzinfo=result.tzinfo
            )
        return result
    
    def __sub__(self, other):
        if isinstance(other, Duration):
            result = _datetime.datetime.__sub__(self, other.as_timedelta())
        elif isinstance(other, DateTime) or isinstance(other, _datetime.datetime):
            result = _datetime.datetime.__sub__(self, other)
            if isinstance(result, _datetime.timedelta):
                return Duration(seconds=result.total_seconds())
            return result
        else:
            result = _datetime.datetime.__sub__(self, other)
        
        if isinstance(result, _datetime.datetime):
            return DateTime(
                result.year, result.month, result.day,
                result.hour, result.minute, result.second, result.microsecond,
                tzinfo=result.tzinfo
            )
        return result
    
    def diff_for_humans(self, other=None, absolute=False, locale='en'):
        """Get a human-readable difference."""
        if other is None:
            from pendulum import now
            other = now(tz=self.tzinfo)
        
        if isinstance(other, str):
            from pendulum import parse
            other = parse(other)
        
        if self.tzinfo is not None and other.tzinfo is None:
            other = other.replace(tzinfo=self.tzinfo)
        elif self.tzinfo is None and other.tzinfo is not None:
            self_copy = self.replace(tzinfo=other.tzinfo)
        else:
            self_copy = self
        
        if self_copy > other:
            diff = self_copy - other
            future = False
        else:
            diff = other - self_copy
            future = True
        
        if isinstance(diff, Duration):
            total_seconds = diff.total_seconds()
        else:
            total_seconds = diff.total_seconds()
        
        abs_seconds = abs(total_seconds)
        
        if abs_seconds < 60:
            count = int(abs_seconds)
            unit = "second" if count == 1 else "seconds"
        elif abs_seconds < 3600:
            count = int(abs_seconds / 60)
            unit = "minute" if count == 1 else "minutes"
        elif abs_seconds < 86400:
            count = int(abs_seconds / 3600)
            unit = "hour" if count == 1 else "hours"
        elif abs_seconds < 604800:
            count = int(abs_seconds / 86400)
            unit = "day" if count == 1 else "days"
        elif abs_seconds < 2592000:
            count = int(abs_seconds / 604800)
            unit = "week" if count == 1 else "weeks"
        elif abs_seconds < 31536000:
            count = int(abs_seconds / 2592000)
            unit = "month" if count == 1 else "months"
        else:
            count = int(abs_seconds / 31536000)
            unit = "year" if count == 1 else "years"
        
        if absolute:
            return f"{count} {unit}"
        
        if future:
            return f"{count} {unit} from now"
        else:
            return f"{count} {unit} ago"
    
    def format(self, fmt, locale='en'):
        """Format the datetime."""
        return format_datetime(self, fmt, locale)
    
    def __repr__(self):
        if self.tzinfo is not None:
            tz_str = f", tz='{self.tzinfo}'"
        else:
            tz_str = ""
        return f"DateTime({self.year}, {self.month}, {self.day}, {self.hour}, {self.minute}, {self.second}, {self.microsecond}{tz_str})"
    
    def __str__(self):
        if self.tzinfo is not None:
            return self.isoformat()
        else:
            return self.isoformat()