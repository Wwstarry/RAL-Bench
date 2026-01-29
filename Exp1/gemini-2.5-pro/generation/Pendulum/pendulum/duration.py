# -*- coding: utf-8 -*-

import datetime as _dt

class Duration:
    """
    A class to represent a duration of time.
    """
    def __init__(self, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0, years=0, months=0):
        total_seconds = seconds + \
                        microseconds / 1e6 + \
                        milliseconds / 1e3 + \
                        minutes * 60 + \
                        hours * 3600 + \
                        days * 86400 + \
                        weeks * 7 * 86400
        
        self._years = years
        self._months = months
        
        # The rest is stored in a timedelta for convenience
        self._timedelta = _dt.timedelta(seconds=total_seconds)

    @property
    def years(self):
        return self._years

    @property
    def months(self):
        return self._months

    @property
    def weeks(self):
        return self.in_weeks()

    @property
    def days(self):
        return self._timedelta.days

    @property
    def hours(self):
        return self.in_hours() % 24

    @property
    def minutes(self):
        return self.in_minutes() % 60

    @property
    def seconds(self):
        return self.in_seconds() % 60

    @property
    def microseconds(self):
        return self._timedelta.microseconds

    @property
    def timedelta(self):
        return self._timedelta

    def in_years(self):
        return self._years + self._months / 12 + self.in_days() / 365.25

    def in_months(self):
        return self._years * 12 + self._months + self.in_days() / 30.4375

    def in_weeks(self):
        return self.in_days() / 7

    def in_days(self):
        return self.total_seconds() / 86400

    def in_hours(self):
        return self.total_seconds() / 3600

    def in_minutes(self):
        return self.total_seconds() / 60

    def in_seconds(self):
        return self.total_seconds()

    def total_seconds(self):
        # Note: This ignores years and months as they are not of fixed duration
        return self._timedelta.total_seconds()

    def __neg__(self):
        neg_duration = Duration()
        neg_duration._years = -self._years
        neg_duration._months = -self._months
        neg_duration._timedelta = -self._timedelta
        return neg_duration

    def __eq__(self, other):
        if not isinstance(other, Duration):
            return NotImplemented
        return self._years == other._years and \
               self._months == other._months and \
               self._timedelta == other._timedelta

    def __repr__(self):
        return f"Duration(years={self._years}, months={self._months}, seconds={self._timedelta.total_seconds()})"