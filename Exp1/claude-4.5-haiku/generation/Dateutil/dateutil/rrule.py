"""
Recurrence rules for generating sequences of dates
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Union, Iterator
from dateutil import tz as tz_module


# Frequency constants
YEARLY = 0
MONTHLY = 1
WEEKLY = 2
DAILY = 3
HOURLY = 4
MINUTELY = 5
SECONDLY = 6

# Weekday constants
class weekday:
    """Represents a weekday with optional week number"""
    
    def __init__(self, weekday: int, n: Optional[int] = None):
        """
        Initialize a weekday.
        
        Args:
            weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday
            n: Week number (1-5 for positive, -1 to -5 for negative from end)
        """
        self.weekday = weekday
        self.n = n
    
    def __repr__(self):
        if self.n is None:
            return f"weekday({self.weekday})"
        return f"weekday({self.weekday}, {self.n})"
    
    def __eq__(self, other):
        if isinstance(other, weekday):
            return self.weekday == other.weekday and self.n == other.n
        return False
    
    def __hash__(self):
        return hash((self.weekday, self.n))


# Weekday instances
MO = weekday(0)
TU = weekday(1)
WE = weekday(2)
TH = weekday(3)
FR = weekday(4)
SA = weekday(5)
SU = weekday(6)


class rrule:
    """
    Recurrence rule for generating sequences of dates.
    
    Supports YEARLY, MONTHLY, WEEKLY, and DAILY frequencies with various
    filtering options like byweekday, bymonthday, etc.
    """
    
    def __init__(self, freq: int, dtstart: Optional[datetime] = None,
                 count: Optional[int] = None, until: Optional[datetime] = None,
                 interval: int = 1, byweekday: Optional[Union[List[weekday], weekday]] = None,
                 bymonthday: Optional[Union[List[int], int]] = None,
                 bymonth: Optional[Union[List[int], int]] = None,
                 byhour: Optional[Union[List[int], int]] = None,
                 byminute: Optional[Union[List[int], int]] = None,
                 bysecond: Optional[Union[List[int], int]] = None,
                 bysetpos: Optional[Union[List[int], int]] = None,
                 wkst: int = 0):
        """
        Initialize an rrule.
        
        Args:
            freq: Frequency (YEARLY, MONTHLY, WEEKLY, DAILY, etc.)
            dtstart: Start datetime
            count: Number of occurrences
            until: End datetime
            interval: Interval between occurrences
            byweekday: Filter by weekday(s)
            bymonthday: Filter by day of month
            bymonth: Filter by month
            byhour: Filter by hour
            byminute: Filter by minute
            bysecond: Filter by second
            bysetpos: Filter by position in set
            wkst: Week start day (0=Monday)
        """
        self.freq = freq
        self.dtstart = dtstart or datetime.now()
        self.count = count
        self.until = until
        self.interval = interval
        self.wkst = wkst
        
        # Normalize list parameters
        self.byweekday = self._normalize_list(byweekday)
        self.bymonthday = self._normalize_list(bymonthday)
        self.bymonth = self._normalize_list(bymonth)
        self.byhour = self._normalize_list(byhour)
        self.byminute = self._normalize_list(byminute)
        self.bysecond = self._normalize_list(bysecond)
        self.bysetpos = self._normalize_list(bysetpos)
    
    def _normalize_list(self, value):
        """Convert single values to lists"""
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            return list(value)
        return [value]
    
    def __iter__(self) -> Iterator[datetime]:
        """Iterate over occurrences"""
        return self._generate()
    
    def _generate(self) -> Iterator[datetime]:
        """Generate occurrences"""
        current = self.dtstart
        count = 0
        
        while True:
            # Check count limit
            if self.count is not None and count >= self.count:
                break
            
            # Check until limit
            if self.until is not None and current > self.until:
                break
            
            # Check if current matches all filters
            if self._matches(current):
                yield current
                count += 1
            
            # Move to next candidate
            current = self._next_candidate(current)
    
    def _matches(self, dt: datetime) -> bool:
        """Check if datetime matches all filters"""
        # Check bymonth
        if self.bymonth is not None and dt.month not in self.bymonth:
            return False
        
        # Check bymonthday
        if self.bymonthday is not None and dt.day not in self.bymonthday:
            return False
        
        # Check byweekday
        if self.byweekday is not None:
            weekday_num = dt.weekday()
            # Convert Python weekday (0=Mon) to our weekday (0=Mon)
            if not any(wd.weekday == weekday_num for wd in self.byweekday):
                return False
        
        # Check byhour
        if self.byhour is not None and dt.hour not in self.byhour:
            return False
        
        # Check byminute
        if self.byminute is not None and dt.minute not in self.byminute:
            return False
        
        # Check bysecond
        if self.bysecond is not None and dt.second not in self.bysecond:
            return False
        
        return True
    
    def _next_candidate(self, dt: datetime) -> datetime:
        """Get the next candidate datetime"""
        if self.freq == DAILY:
            return dt + timedelta(days=self.interval)
        elif self.freq == WEEKLY:
            return dt + timedelta(weeks=self.interval)
        elif self.freq == MONTHLY:
            # Add months
            month = dt.month + self.interval
            year = dt.year
            while month > 12:
                month -= 12
                year += 1
            
            # Handle day overflow
            day = dt.day
            while True:
                try:
                    return dt.replace(year=year, month=month, day=day)
                except ValueError:
                    day -= 1
        elif self.freq == YEARLY:
            return dt.replace(year=dt.year + self.interval)
        elif self.freq == HOURLY:
            return dt + timedelta(hours=self.interval)
        elif self.freq == MINUTELY:
            return dt + timedelta(minutes=self.interval)
        elif self.freq == SECONDLY:
            return dt + timedelta(seconds=self.interval)
        
        return dt + timedelta(days=1)
    
    def __repr__(self):
        freq_names = {
            YEARLY: 'YEARLY',
            MONTHLY: 'MONTHLY',
            WEEKLY: 'WEEKLY',
            DAILY: 'DAILY',
            HOURLY: 'HOURLY',
            MINUTELY: 'MINUTELY',
            SECONDLY: 'SECONDLY',
        }
        return f"rrule({freq_names.get(self.freq, self.freq)}, dtstart={self.dtstart!r})"