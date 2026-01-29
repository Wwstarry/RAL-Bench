import re
import time
import calendar
from datetime import datetime as std_datetime, timedelta, timezone as std_timezone
from typing import Optional, Union, Tuple, Any, Dict
from .timezone import Timezone, FixedTimezone
from .duration import Duration
from .formatting import Formatter

class DateTime:
    """Timezone-aware datetime compatible with Pendulum."""
    
    __slots__ = ('_datetime', '_timezone', '_formatter')
    
    def __init__(
        self,
        year: int,
        month: int,
        day: int,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        microsecond: int = 0,
        tz: Optional[Union[str, Timezone]] = None,
        fold: int = 0
    ):
        if tz is None:
            self._timezone = Timezone("UTC")
        elif isinstance(tz, str):
            self._timezone = Timezone(tz)
        else:
            self._timezone = tz
            
        self._datetime = std_datetime(
            year, month, day, hour, minute, second, microsecond,
            tzinfo=self._timezone._tzinfo, fold=fold
        )
        self._formatter = Formatter()
    
    @classmethod
    def create(
        cls,
        year: int,
        month: int,
        day: int,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        microsecond: int = 0,
        tz: Optional[Union[str, Timezone]] = None,
        fold: int = 0
    ) -> 'DateTime':
        """Create a new DateTime instance."""
        return cls(year, month, day, hour, minute, second, microsecond, tz, fold)
    
    @classmethod
    def now(cls, tz: Optional[Union[str, Timezone]] = None) -> 'DateTime':
        """Create DateTime from current time."""
        if tz is None:
            tz_obj = Timezone("UTC")
        elif isinstance(tz, str):
            tz_obj = Timezone(tz)
        else:
            tz_obj = tz
            
        dt = std_datetime.now(tz_obj._tzinfo)
        return cls._from_std_datetime(dt, tz_obj)
    
    @classmethod
    def today(cls, tz: Optional[Union[str, Timezone]] = None) -> 'DateTime':
        """Get today at midnight."""
        now = cls.now(tz)
        return cls(now.year, now.month, now.day, tz=tz)
    
    @classmethod
    def yesterday(cls, tz: Optional[Union[str, Timezone]] = None) -> 'DateTime':
        """Get yesterday at midnight."""
        today = cls.today(tz)
        return today.subtract(days=1)
    
    @classmethod
    def tomorrow(cls, tz: Optional[Union[str, Timezone]] = None) -> 'DateTime':
        """Get tomorrow at midnight."""
        today = cls.today(tz)
        return today.add(days=1)
    
    @classmethod
    def parse(
        cls,
        text: str,
        tz: Optional[Union[str, Timezone]] = None,
        strict: bool = True
    ) -> 'DateTime':
        """Parse ISO-8601 string."""
        # Simplified ISO-8601 parser
        patterns = [
            r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(?:Z|([+-]\d{2}):?(\d{2})?)?$',
            r'^(\d{4})-(\d{2})-(\d{2})$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # Date only
                    year, month, day = map(int, groups)
                    return cls(year, month, day, tz=tz)
                else:  # Full datetime
                    year, month, day, hour, minute, second = map(int, groups[:6])
                    microsecond = int(groups[6]) if groups[6] else 0
                    tz_offset = groups[7]
                    
                    if tz_offset is None:
                        tz_obj = Timezone("UTC") if tz is None else (Timezone(tz) if isinstance(tz, str) else tz)
                    elif tz_offset == 'Z':
                        tz_obj = Timezone("UTC")
                    else:
                        tz_hour = int(tz_offset)
                        tz_minute = int(groups[8]) if groups[8] else 0
                        offset = tz_hour * 3600 + tz_minute * 60
                        if tz_hour < 0:
                            offset = -offset
                        tz_obj = FixedTimezone(offset)
                    
                    return cls(year, month, day, hour, minute, second, microsecond, tz_obj)
        
        if strict:
            raise ValueError(f"Unable to parse: {text}")
        return cls.now(tz)
    
    @classmethod
    def _from_std_datetime(cls, dt: std_datetime, tz: Timezone) -> 'DateTime':
        """Create from std datetime."""
        return cls(
            dt.year, dt.month, dt.day,
            dt.hour, dt.minute, dt.second, dt.microsecond,
            tz, dt.fold
        )
    
    @property
    def year(self) -> int:
        return self._datetime.year
    
    @property
    def month(self) -> int:
        return self._datetime.month
    
    @property
    def day(self) -> int:
        return self._datetime.day
    
    @property
    def hour(self) -> int:
        return self._datetime.hour
    
    @property
    def minute(self) -> int:
        return self._datetime.minute
    
    @property
    def second(self) -> int:
        return self._datetime.second
    
    @property
    def microsecond(self) -> int:
        return self._datetime.microsecond
    
    @property
    def tzinfo(self):
        return self._timezone._tzinfo
    
    @property
    def timezone(self) -> Timezone:
        return self._timezone
    
    @property
    def offset(self) -> int:
        """Timezone offset in seconds."""
        return self._timezone.offset(self._datetime)
    
    def in_timezone(self, tz: Union[str, Timezone]) -> 'DateTime':
        """Convert to different timezone."""
        if isinstance(tz, str):
            tz = Timezone(tz)
        
        # Convert through UTC
        utc_dt = self._datetime.astimezone(std_timezone.utc)
        new_dt = utc_dt.astimezone(tz._tzinfo)
        return self._from_std_datetime(new_dt, tz)
    
    def add(
        self,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0
    ) -> 'DateTime':
        """Add time to datetime."""
        # Handle months and years separately due to variable lengths
        new_year = self.year + years
        new_month = self.month + months
        
        # Adjust month overflow
        while new_month > 12:
            new_year += 1
            new_month -= 12
        while new_month < 1:
            new_year -= 1
            new_month += 12
        
        # Get days in month
        max_day = calendar.monthrange(new_year, new_month)[1]
        new_day = min(self.day, max_day)
        
        # Create base datetime
        dt = std_datetime(
            new_year, new_month, new_day,
            self.hour, self.minute, self.second, self.microsecond,
            tzinfo=self.tzinfo, fold=self._datetime.fold
        )
        
        # Add other units
        delta = timedelta(
            weeks=weeks, days=days,
            hours=hours, minutes=minutes,
            seconds=seconds, microseconds=microseconds
        )
        dt += delta
        
        return self._from_std_datetime(dt, self._timezone)
    
    def subtract(
        self,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0
    ) -> 'DateTime':
        """Subtract time from datetime."""
        return self.add(
            years=-years, months=-months,
            weeks=-weeks, days=-days,
            hours=-hours, minutes=-minutes,
            seconds=-seconds, microseconds=-microseconds
        )
    
    def diff(self, other: 'DateTime', absolute: bool = True) -> Duration:
        """Calculate difference between two datetimes."""
        if not isinstance(other, DateTime):
            other = DateTime.parse(str(other))
        
        delta = self._datetime - other._datetime
        if absolute:
            delta = abs(delta)
        
        return Duration(seconds=delta.total_seconds())
    
    def diff_for_humans(
        self,
        other: Optional['DateTime'] = None,
        absolute: bool = True,
        locale: str = 'en'
    ) -> str:
        """Get human-readable difference."""
        if other is None:
            other = self.now(self._timezone)
        
        diff = self.diff(other, absolute)
        return self._formatter.format_diff(diff, locale)
    
    def __sub__(self, other: Union['DateTime', Duration]) -> Union[Duration, 'DateTime']:
        if isinstance(other, DateTime):
            return self.diff(other)
        elif isinstance(other, Duration):
            return self.subtract(
                years=other.years, months=other.months,
                weeks=other.weeks, days=other.days,
                hours=other.hours, minutes=other.minutes,
                seconds=other.seconds, microseconds=other.microseconds
            )
        raise TypeError(f"Unsupported type: {type(other)}")
    
    def __add__(self, other: Duration) -> 'DateTime':
        if isinstance(other, Duration):
            return self.add(
                years=other.years, months=other.months,
                weeks=other.weeks, days=other.days,
                hours=other.hours, minutes=other.minutes,
                seconds=other.seconds, microseconds=other.microseconds
            )
        raise TypeError(f"Unsupported type: {type(other)}")
    
    def __str__(self) -> str:
        return self.isoformat()
    
    def isoformat(self) -> str:
        """Return ISO-8601 formatted string."""
        dt_str = self._datetime.isoformat()
        if dt_str.endswith('+00:00'):
            dt_str = dt_str[:-6] + 'Z'
        return dt_str
    
    def __repr__(self) -> str:
        return f"DateTime({self.year}, {self.month}, {self.day}, {self.hour}, {self.minute}, {self.second}, {self.microsecond}, tz={self._timezone})"
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, DateTime):
            return False
        return self._datetime == other._datetime
    
    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, DateTime):
            raise TypeError(f"Can't compare DateTime with {type(other)}")
        return self._datetime < other._datetime
    
    def __le__(self, other: Any) -> bool:
        if not isinstance(other, DateTime):
            raise TypeError(f"Can't compare DateTime with {type(other)}")
        return self._datetime <= other._datetime
    
    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, DateTime):
            raise TypeError(f"Can't compare DateTime with {type(other)}")
        return self._datetime > other._datetime
    
    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, DateTime):
            raise TypeError(f"Can't compare DateTime with {type(other)}")
        return self._datetime >= other._datetime