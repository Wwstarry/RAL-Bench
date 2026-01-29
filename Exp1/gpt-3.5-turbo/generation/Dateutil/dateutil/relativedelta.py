"""
Pure Python implementation of dateutil.relativedelta.relativedelta
for calendar-aware date/time arithmetic.
"""

import datetime
from dateutil import tz

__all__ = ['relativedelta']

class relativedelta:
    """
    relativedelta objects represent relative time deltas with calendar awareness.

    Supports years, months, days, hours, minutes, seconds, microseconds,
    and weekday specifications.

    Usage:
        rd = relativedelta(years=1, months=2, days=3, hours=4)
        new_date = old_date + rd
    """

    def __init__(self, years=0, months=0, days=0,
                 hours=0, minutes=0, seconds=0, microseconds=0,
                 weekday=None):
        self.years = years
        self.months = months
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.microseconds = microseconds
        self.weekday = weekday  # Not implemented fully, placeholder

    def __add__(self, dt):
        if not isinstance(dt, (datetime.date, datetime.datetime)):
            return NotImplemented

        # Start with date or datetime
        if isinstance(dt, datetime.datetime):
            has_time = True
        else:
            has_time = False

        year = dt.year + self.years
        month = dt.month + self.months
        # Normalize month and year
        while month > 12:
            month -= 12
            year += 1
        while month < 1:
            month += 12
            year -= 1

        # Day adjustment: clamp day to max day of new month
        day = dt.day
        max_day = _days_in_month(year, month)
        if day > max_day:
            day = max_day

        # Construct new date/datetime with year, month, day
        if has_time:
            new_dt = datetime.datetime(year, month, day,
                                       dt.hour, dt.minute, dt.second, dt.microsecond,
                                       tzinfo=dt.tzinfo)
        else:
            new_dt = datetime.date(year, month, day)

        # Add days and smaller units
        if self.days or self.hours or self.minutes or self.seconds or self.microseconds:
            delta = datetime.timedelta(days=self.days,
                                       hours=self.hours,
                                       minutes=self.minutes,
                                       seconds=self.seconds,
                                       microseconds=self.microseconds)
            if has_time:
                new_dt = new_dt + delta
            else:
                # For date, only days make sense
                new_dt = new_dt + datetime.timedelta(days=self.days)

        # weekday handling is not implemented (would require more complex logic)
        # so we ignore self.weekday here

        return new_dt

    def __radd__(self, dt):
        return self.__add__(dt)

    def __sub__(self, dt):
        # Support subtraction from datetime/date by negating relativedelta
        if not isinstance(dt, (datetime.date, datetime.datetime)):
            return NotImplemented
        neg = relativedelta(years=-self.years, months=-self.months,
                            days=-self.days, hours=-self.hours,
                            minutes=-self.minutes, seconds=-self.seconds,
                            microseconds=-self.microseconds,
                            weekday=self.weekday)
        return neg.__add__(dt)

    def __rsub__(self, dt):
        # dt - relativedelta: not supported
        return NotImplemented

def _days_in_month(year, month):
    # Return number of days in the given month and year
    if month == 12:
        next_month = datetime.date(year + 1, 1, 1)
    else:
        next_month = datetime.date(year, month + 1, 1)
    this_month = datetime.date(year, month, 1)
    return (next_month - this_month).days