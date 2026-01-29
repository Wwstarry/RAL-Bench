"""
Relative delta for date arithmetic
"""

from datetime import datetime, date, timedelta
from typing import Union, Optional


class relativedelta:
    """
    Represents a relative time delta that can handle months and years.
    
    This is useful for calendar-aware arithmetic where you want to add
    months or years to a date, rather than just days.
    """
    
    def __init__(self, dt1: Optional[Union[datetime, date]] = None,
                 dt2: Optional[Union[datetime, date]] = None,
                 years: int = 0, months: int = 0, days: int = 0,
                 weeks: int = 0, hours: int = 0, minutes: int = 0,
                 seconds: int = 0, microseconds: int = 0):
        """
        Initialize a relativedelta.
        
        Can be used in two ways:
        1. relativedelta(dt1, dt2) - difference between two dates
        2. relativedelta(years=..., months=..., days=..., etc.) - offset
        """
        if dt1 is not None and dt2 is not None:
            # Difference mode
            self._init_from_difference(dt1, dt2)
        else:
            # Offset mode
            self.years = years
            self.months = months
            self.days = days
            self.weeks = weeks
            self.hours = hours
            self.minutes = minutes
            self.seconds = seconds
            self.microseconds = microseconds
    
    def _init_from_difference(self, dt1: Union[datetime, date], dt2: Union[datetime, date]):
        """Initialize from the difference between two dates"""
        # Convert dates to datetimes if needed
        if isinstance(dt1, date) and not isinstance(dt1, datetime):
            dt1 = datetime.combine(dt1, datetime.min.time())
        if isinstance(dt2, date) and not isinstance(dt2, datetime):
            dt2 = datetime.combine(dt2, datetime.min.time())
        
        # Calculate the difference
        self.years = 0
        self.months = 0
        self.days = 0
        self.weeks = 0
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
        self.microseconds = 0
        
        # Simple approach: calculate years and months
        if dt1 > dt2:
            dt1, dt2 = dt2, dt1
            sign = -1
        else:
            sign = 1
        
        # Calculate years
        years = dt2.year - dt1.year
        if (dt2.month, dt2.day) < (dt1.month, dt1.day):
            years -= 1
        self.years = years * sign
        
        # Calculate months
        dt1_adjusted = self._add_years(dt1, years)
        months = dt2.month - dt1_adjusted.month
        if dt2.day < dt1_adjusted.day:
            months -= 1
        self.months = months * sign
        
        # Calculate remaining days
        dt1_adjusted = self._add_months(dt1_adjusted, months)
        delta = dt2 - dt1_adjusted
        
        self.days = delta.days * sign
        self.seconds = delta.seconds * sign
        self.microseconds = delta.microseconds * sign
    
    def __add__(self, other: Union[datetime, date]) -> Union[datetime, date]:
        """Add this relativedelta to a date or datetime"""
        if isinstance(other, datetime):
            return self._add_to_datetime(other)
        elif isinstance(other, date):
            return self._add_to_date(other)
        return NotImplemented
    
    def __radd__(self, other: Union[datetime, date]) -> Union[datetime, date]:
        """Right add"""
        return self.__add__(other)
    
    def __sub__(self, other):
        """Subtract"""
        if isinstance(other, relativedelta):
            return relativedelta(
                years=self.years - other.years,
                months=self.months - other.months,
                days=self.days - other.days,
                weeks=self.weeks - other.weeks,
                hours=self.hours - other.hours,
                minutes=self.minutes - other.minutes,
                seconds=self.seconds - other.seconds,
                microseconds=self.microseconds - other.microseconds,
            )
        return NotImplemented
    
    def __rsub__(self, other: Union[datetime, date]) -> Union[datetime, date]:
        """Right subtract"""
        if isinstance(other, (datetime, date)):
            # other - self
            neg = relativedelta(
                years=-self.years,
                months=-self.months,
                days=-self.days,
                weeks=-self.weeks,
                hours=-self.hours,
                minutes=-self.minutes,
                seconds=-self.seconds,
                microseconds=-self.microseconds,
            )
            return neg + other
        return NotImplemented
    
    def _add_to_datetime(self, dt: datetime) -> datetime:
        """Add this relativedelta to a datetime"""
        # Add years and months
        year = dt.year + self.years
        month = dt.month + self.months
        
        # Normalize month overflow
        while month > 12:
            month -= 12
            year += 1
        while month < 1:
            month += 12
            year -= 1
        
        # Handle day overflow (e.g., Jan 31 + 1 month = Feb 28/29)
        day = dt.day
        while True:
            try:
                result = dt.replace(year=year, month=month, day=day)
                break
            except ValueError:
                day -= 1
        
        # Add remaining time components
        total_days = self.days + self.weeks * 7
        total_seconds = (self.hours * 3600 + self.minutes * 60 + self.seconds)
        
        delta = timedelta(days=total_days, seconds=total_seconds, microseconds=self.microseconds)
        result = result + delta
        
        return result
    
    def _add_to_date(self, d: date) -> date:
        """Add this relativedelta to a date"""
        # Convert to datetime, add, and convert back
        dt = datetime.combine(d, datetime.min.time())
        result = self._add_to_datetime(dt)
        return result.date()
    
    def _add_years(self, dt: datetime, years: int) -> datetime:
        """Add years to a datetime"""
        try:
            return dt.replace(year=dt.year + years)
        except ValueError:
            # Handle Feb 29 in leap years
            return dt.replace(year=dt.year + years, day=28)
    
    def _add_months(self, dt: datetime, months: int) -> datetime:
        """Add months to a datetime"""
        month = dt.month + months
        year = dt.year
        
        while month > 12:
            month -= 12
            year += 1
        while month < 1:
            month += 12
            year -= 1
        
        day = dt.day
        while True:
            try:
                return dt.replace(year=year, month=month, day=day)
            except ValueError:
                day -= 1
    
    def __repr__(self):
        parts = []
        if self.years:
            parts.append(f"years={self.years}")
        if self.months:
            parts.append(f"months={self.months}")
        if self.days:
            parts.append(f"days={self.days}")
        if self.weeks:
            parts.append(f"weeks={self.weeks}")
        if self.hours:
            parts.append(f"hours={self.hours}")
        if self.minutes:
            parts.append(f"minutes={self.minutes}")
        if self.seconds:
            parts.append(f"seconds={self.seconds}")
        if self.microseconds:
            parts.append(f"microseconds={self.microseconds}")
        
        if not parts:
            return "relativedelta()"
        return f"relativedelta({', '.join(parts)})"