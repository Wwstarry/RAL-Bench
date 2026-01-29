"""
Recurrence rule implementation for generating datetime sequences.
"""

from datetime import datetime, timedelta
import calendar


# Frequency constants
YEARLY = 0
MONTHLY = 1
WEEKLY = 2
DAILY = 3
HOURLY = 4
MINUTELY = 5
SECONDLY = 6


class weekday:
    """Represents a weekday with optional occurrence number."""
    
    def __init__(self, weekday, n=None):
        """
        Initialize a weekday.
        
        Args:
            weekday: 0-6 for Monday-Sunday
            n: Optional occurrence number (e.g., 1 for first, -1 for last)
        """
        self.weekday = weekday
        self.n = n
    
    def __eq__(self, other):
        if isinstance(other, weekday):
            return self.weekday == other.weekday and self.n == other.n
        return False
    
    def __repr__(self):
        days = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
        if self.n is None:
            return days[self.weekday]
        return f"{days[self.weekday]}({self.n})"


# Weekday constants
MO = weekday(0)
TU = weekday(1)
WE = weekday(2)
TH = weekday(3)
FR = weekday(4)
SA = weekday(5)
SU = weekday(6)


class rrule:
    """
    Recurrence rule for generating sequences of datetimes.
    """
    
    def __init__(self, freq, dtstart=None, interval=1, wkst=None, count=None,
                 until=None, bysetpos=None, bymonth=None, bymonthday=None,
                 byyearday=None, byweekno=None, byweekday=None, byhour=None,
                 byminute=None, bysecond=None, byeaster=None):
        """
        Initialize a recurrence rule.
        
        Args:
            freq: Frequency constant (DAILY, WEEKLY, etc.)
            dtstart: Start datetime
            interval: Interval between occurrences
            count: Maximum number of occurrences
            until: End datetime
            byweekday: List of weekday constraints
            byhour: List of hour constraints
            byminute: List of minute constraints
            bysecond: List of second constraints
        """
        self.freq = freq
        self.dtstart = dtstart or datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.interval = interval
        self.count = count
        self.until = until
        self.byweekday = byweekday
        self.byhour = byhour
        self.byminute = byminute
        self.bysecond = bysecond
        self.bymonth = bymonth
        self.bymonthday = bymonthday
        
        # Normalize byweekday to list of weekday numbers
        if self.byweekday is not None:
            if not isinstance(self.byweekday, (list, tuple)):
                self.byweekday = [self.byweekday]
            # Extract weekday numbers
            self._weekday_nums = []
            for wd in self.byweekday:
                if isinstance(wd, weekday):
                    self._weekday_nums.append(wd.weekday)
                else:
                    self._weekday_nums.append(wd)
        else:
            self._weekday_nums = None
    
    def __iter__(self):
        """Iterate over occurrences."""
        current = self.dtstart
        count = 0
        
        while True:
            # Check count limit
            if self.count is not None and count >= self.count:
                break
            
            # Check until limit
            if self.until is not None and current > self.until:
                break
            
            # Check if current datetime matches constraints
            if self._matches_constraints(current):
                yield current
                count += 1
            
            # Advance to next candidate
            current = self._advance(current)
            
            # Safety check to prevent infinite loops
            if count > 10000:
                break
    
    def _matches_constraints(self, dt):
        """Check if a datetime matches all constraints."""
        # Check weekday constraint
        if self._weekday_nums is not None:
            if dt.weekday() not in self._weekday_nums:
                return False
        
        # Check hour constraint
        if self.byhour is not None:
            if dt.hour not in self.byhour:
                return False
        
        # Check minute constraint
        if self.byminute is not None:
            if dt.minute not in self.byminute:
                return False
        
        # Check second constraint
        if self.bysecond is not None:
            if dt.second not in self.bysecond:
                return False
        
        return True
    
    def _advance(self, dt):
        """Advance to the next candidate datetime."""
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
            max_day = calendar.monthrange(year, month)[1]
            day = min(dt.day, max_day)
            return dt.replace(year=year, month=month, day=day)
        elif self.freq == YEARLY:
            return dt.replace(year=dt.year + self.interval)
        elif self.freq == HOURLY:
            return dt + timedelta(hours=self.interval)
        elif self.freq == MINUTELY:
            return dt + timedelta(minutes=self.interval)
        elif self.freq == SECONDLY:
            return dt + timedelta(seconds=self.interval)
        else:
            return dt + timedelta(days=1)
    
    def between(self, after, before, inc=False):
        """
        Return occurrences between two datetimes.
        
        Args:
            after: Start datetime (exclusive unless inc=True)
            before: End datetime (exclusive unless inc=True)
            inc: If True, include boundaries
            
        Returns:
            List of datetime objects
        """
        result = []
        for dt in self:
            if inc:
                if dt < after:
                    continue
                if dt > before:
                    break
            else:
                if dt <= after:
                    continue
                if dt >= before:
                    break
            result.append(dt)
        return result
    
    def __getitem__(self, index):
        """Get occurrence by index."""
        if isinstance(index, slice):
            result = []
            for i, dt in enumerate(self):
                if index.start is not None and i < index.start:
                    continue
                if index.stop is not None and i >= index.stop:
                    break
                result.append(dt)
            return result
        else:
            for i, dt in enumerate(self):
                if i == index:
                    return dt
            raise IndexError("rrule index out of range")