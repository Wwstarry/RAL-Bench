"""
Relative delta implementation for calendar-aware date arithmetic.
"""

from datetime import datetime, timedelta
import calendar


class relativedelta:
    """
    Represents a relative delta between two datetime objects.
    Supports calendar-aware arithmetic like adding months or years.
    """
    
    def __init__(self, dt1=None, dt2=None, years=0, months=0, days=0, 
                 weeks=0, hours=0, minutes=0, seconds=0, microseconds=0,
                 year=None, month=None, day=None, hour=None, minute=None,
                 second=None, microsecond=None, weekday=None):
        """
        Initialize a relativedelta.
        
        Can be initialized with two datetime objects to compute the difference,
        or with explicit delta values.
        
        Args:
            dt1, dt2: datetime objects to compute difference
            years, months, days, weeks, hours, minutes, seconds, microseconds: relative deltas
            year, month, day, hour, minute, second, microsecond: absolute values
            weekday: weekday specification
        """
        if dt1 and dt2:
            # Compute difference between two datetimes
            self.years = 0
            self.months = 0
            self.days = 0
            self.hours = 0
            self.minutes = 0
            self.seconds = 0
            self.microseconds = 0
            
            # Calculate year and month difference
            year_diff = dt1.year - dt2.year
            month_diff = dt1.month - dt2.month
            
            total_months = year_diff * 12 + month_diff
            self.years = total_months // 12
            self.months = total_months % 12
            
            # Calculate day difference
            # Create a datetime with the same year/month as dt1 but day from dt2
            try:
                temp_dt = datetime(dt1.year, dt1.month, dt2.day, dt2.hour, 
                                 dt2.minute, dt2.second, dt2.microsecond)
            except ValueError:
                # Day doesn't exist in target month
                last_day = calendar.monthrange(dt1.year, dt1.month)[1]
                temp_dt = datetime(dt1.year, dt1.month, last_day, dt2.hour,
                                 dt2.minute, dt2.second, dt2.microsecond)
            
            delta = dt1 - temp_dt
            self.days = delta.days
            self.seconds = delta.seconds
            self.microseconds = delta.microseconds
            
            self.year = None
            self.month = None
            self.day = None
            self.hour = None
            self.minute = None
            self.second = None
            self.microsecond = None
            self.weekday = None
        else:
            # Store relative values
            self.years = years
            self.months = months
            self.days = days + weeks * 7
            self.hours = hours
            self.minutes = minutes
            self.seconds = seconds
            self.microseconds = microseconds
            
            # Store absolute values
            self.year = year
            self.month = month
            self.day = day
            self.hour = hour
            self.minute = minute
            self.second = second
            self.microsecond = microsecond
            self.weekday = weekday
    
    def __add__(self, other):
        """Add this relativedelta to a datetime or another relativedelta."""
        if isinstance(other, datetime):
            return self._apply_to_datetime(other)
        elif isinstance(other, relativedelta):
            return relativedelta(
                years=self.years + other.years,
                months=self.months + other.months,
                days=self.days + other.days,
                hours=self.hours + other.hours,
                minutes=self.minutes + other.minutes,
                seconds=self.seconds + other.seconds,
                microseconds=self.microseconds + other.microseconds
            )
        return NotImplemented
    
    def __radd__(self, other):
        """Support datetime + relativedelta."""
        if isinstance(other, datetime):
            return self._apply_to_datetime(other)
        return NotImplemented
    
    def __sub__(self, other):
        """Subtract another relativedelta."""
        if isinstance(other, relativedelta):
            return relativedelta(
                years=self.years - other.years,
                months=self.months - other.months,
                days=self.days - other.days,
                hours=self.hours - other.hours,
                minutes=self.minutes - other.minutes,
                seconds=self.seconds - other.seconds,
                microseconds=self.microseconds - other.microseconds
            )
        return NotImplemented
    
    def __rsub__(self, other):
        """Support datetime - relativedelta."""
        if isinstance(other, datetime):
            # Negate and apply
            return self.__neg__()._apply_to_datetime(other)
        return NotImplemented
    
    def __neg__(self):
        """Negate this relativedelta."""
        return relativedelta(
            years=-self.years,
            months=-self.months,
            days=-self.days,
            hours=-self.hours,
            minutes=-self.minutes,
            seconds=-self.seconds,
            microseconds=-self.microseconds,
            year=self.year,
            month=self.month,
            day=self.day,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            microsecond=self.microsecond,
            weekday=self.weekday
        )
    
    def _apply_to_datetime(self, dt):
        """Apply this relativedelta to a datetime object."""
        # Start with the original datetime
        year = dt.year
        month = dt.month
        day = dt.day
        hour = dt.hour
        minute = dt.minute
        second = dt.second
        microsecond = dt.microsecond
        
        # Apply relative year and month changes
        year += self.years
        month += self.months
        
        # Handle month overflow/underflow
        while month > 12:
            month -= 12
            year += 1
        while month < 1:
            month += 12
            year -= 1
        
        # Apply absolute values if specified
        if self.year is not None:
            year = self.year
        if self.month is not None:
            month = self.month
        if self.day is not None:
            day = self.day
        if self.hour is not None:
            hour = self.hour
        if self.minute is not None:
            minute = self.minute
        if self.second is not None:
            second = self.second
        if self.microsecond is not None:
            microsecond = self.microsecond
        
        # Ensure day is valid for the month
        max_day = calendar.monthrange(year, month)[1]
        if day > max_day:
            day = max_day
        
        # Create new datetime
        result = datetime(year, month, day, hour, minute, second, microsecond, tzinfo=dt.tzinfo)
        
        # Apply day/time deltas
        if self.days or self.hours or self.minutes or self.seconds or self.microseconds:
            delta = timedelta(
                days=self.days,
                hours=self.hours,
                minutes=self.minutes,
                seconds=self.seconds,
                microseconds=self.microseconds
            )
            result = result + delta
        
        return result
    
    def __eq__(self, other):
        """Check equality with another relativedelta."""
        if not isinstance(other, relativedelta):
            return False
        return (self.years == other.years and
                self.months == other.months and
                self.days == other.days and
                self.hours == other.hours and
                self.minutes == other.minutes and
                self.seconds == other.seconds and
                self.microseconds == other.microseconds and
                self.year == other.year and
                self.month == other.month and
                self.day == other.day and
                self.hour == other.hour and
                self.minute == other.minute and
                self.second == other.second and
                self.microsecond == other.microsecond)
    
    def __repr__(self):
        parts = []
        if self.years:
            parts.append(f"years={self.years}")
        if self.months:
            parts.append(f"months={self.months}")
        if self.days:
            parts.append(f"days={self.days}")
        if self.hours:
            parts.append(f"hours={self.hours}")
        if self.minutes:
            parts.append(f"minutes={self.minutes}")
        if self.seconds:
            parts.append(f"seconds={self.seconds}")
        if self.microseconds:
            parts.append(f"microseconds={self.microseconds}")
        return f"relativedelta({', '.join(parts)})"