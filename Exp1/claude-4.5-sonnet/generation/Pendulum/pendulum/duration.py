"""
Duration class implementation.
"""

import datetime as dt


class Duration(dt.timedelta):
    """
    A Duration class that extends timedelta with additional functionality.
    """

    def __new__(
        cls,
        days=0,
        seconds=0,
        microseconds=0,
        milliseconds=0,
        minutes=0,
        hours=0,
        weeks=0,
        years=0,
        months=0,
    ):
        """
        Create a new Duration instance.
        """
        # Convert years and months to days (approximate)
        total_days = days + weeks * 7 + years * 365 + months * 30
        
        instance = dt.timedelta.__new__(
            cls,
            days=total_days,
            seconds=seconds,
            microseconds=microseconds,
            milliseconds=milliseconds,
            minutes=minutes,
            hours=hours,
        )
        
        # Store original values
        instance._years = years
        instance._months = months
        
        return instance

    @property
    def years(self):
        """
        Get the number of years.
        """
        return getattr(self, '_years', 0)

    @property
    def months(self):
        """
        Get the number of months.
        """
        return getattr(self, '_months', 0)

    @property
    def weeks(self):
        """
        Get the number of weeks.
        """
        return self.days // 7

    @property
    def remaining_days(self):
        """
        Get the remaining days after weeks.
        """
        return self.days % 7

    @property
    def hours(self):
        """
        Get the number of hours.
        """
        return self.seconds // 3600

    @property
    def minutes(self):
        """
        Get the number of minutes.
        """
        return (self.seconds % 3600) // 60

    @property
    def remaining_seconds(self):
        """
        Get the remaining seconds after minutes.
        """
        return self.seconds % 60

    def in_days(self):
        """
        Get the total duration in days.
        """
        return self.total_seconds() / 86400

    def in_hours(self):
        """
        Get the total duration in hours.
        """
        return self.total_seconds() / 3600

    def in_minutes(self):
        """
        Get the total duration in minutes.
        """
        return self.total_seconds() / 60

    def in_seconds(self):
        """
        Get the total duration in seconds.
        """
        return self.total_seconds()

    def in_words(self, locale=None):
        """
        Get a human-readable representation of the duration.
        """
        parts = []
        
        if self.years:
            parts.append(f"{self.years} year{'s' if self.years != 1 else ''}")
        
        if self.months:
            parts.append(f"{self.months} month{'s' if self.months != 1 else ''}")
        
        weeks = self.weeks
        if weeks:
            parts.append(f"{weeks} week{'s' if weeks != 1 else ''}")
        
        days = self.remaining_days
        if days:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        
        hours = self.hours
        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        
        minutes = self.minutes
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        
        seconds = self.remaining_seconds
        if seconds or not parts:
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return f"{parts[0]} and {parts[1]}"
        else:
            return ", ".join(parts[:-1]) + f", and {parts[-1]}"

    def __repr__(self):
        return f"Duration({self.in_words()})"

    def __str__(self):
        return self.in_words()

    def __abs__(self):
        """
        Get the absolute value of the duration.
        """
        if self.total_seconds() >= 0:
            return self
        return Duration(
            days=-self.days,
            seconds=-self.seconds,
            microseconds=-self.microseconds,
        )

    def __neg__(self):
        """
        Negate the duration.
        """
        result = dt.timedelta.__neg__(self)
        return Duration(
            days=result.days,
            seconds=result.seconds,
            microseconds=result.microseconds,
        )

    def __add__(self, other):
        """
        Add another duration or timedelta.
        """
        result = dt.timedelta.__add__(self, other)
        if isinstance(result, dt.timedelta):
            return Duration(
                days=result.days,
                seconds=result.seconds,
                microseconds=result.microseconds,
            )
        return result

    def __sub__(self, other):
        """
        Subtract another duration or timedelta.
        """
        result = dt.timedelta.__sub__(self, other)
        if isinstance(result, dt.timedelta):
            return Duration(
                days=result.days,
                seconds=result.seconds,
                microseconds=result.microseconds,
            )
        return result

    def __mul__(self, other):
        """
        Multiply the duration by a number.
        """
        result = dt.timedelta.__mul__(self, other)
        if isinstance(result, dt.timedelta):
            return Duration(
                days=result.days,
                seconds=result.seconds,
                microseconds=result.microseconds,
            )
        return result

    def __truediv__(self, other):
        """
        Divide the duration by a number.
        """
        result = dt.timedelta.__truediv__(self, other)
        if isinstance(result, dt.timedelta):
            return Duration(
                days=result.days,
                seconds=result.seconds,
                microseconds=result.microseconds,
            )
        return result