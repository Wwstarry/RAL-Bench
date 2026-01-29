"""
Pure Python implementation of dateutil.rrule module with rrule class,
constants DAILY, WEEKLY, and weekday constants MO, TU, WE, TH, FR.
"""

import datetime
from dateutil import tz

__all__ = ['rrule', 'DAILY', 'WEEKLY', 'MO', 'TU', 'WE', 'TH', 'FR']

# Frequency constants
DAILY = 3
WEEKLY = 2

# Weekday constants with byweekday support
class _Weekday:
    def __init__(self, weekday):
        self.weekday = weekday  # Monday=0 ... Sunday=6

    def __eq__(self, other):
        if isinstance(other, _Weekday):
            return self.weekday == other.weekday
        return False

    def __hash__(self):
        return hash(self.weekday)

    def __repr__(self):
        names = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
        return names[self.weekday]

    def __call__(self, n=None):
        # Support nth weekday (not fully implemented)
        # For now, just return self ignoring n
        return self

MO = _Weekday(0)
TU = _Weekday(1)
WE = _Weekday(2)
TH = _Weekday(3)
FR = _Weekday(4)

class rrule:
    """
    Recurrence rule iterator.

    Parameters:
        freq: frequency constant (DAILY, WEEKLY)
        dtstart: datetime to start recurrence from
        interval: step between recurrences (default 1)
        count: number of occurrences (default None)
        until: datetime to stop recurrence (default None)
        byweekday: list of weekdays to filter (default None)

    Usage:
        rule = rrule(DAILY, dtstart=datetime.datetime(2020,1,1), count=5)
        for dt in rule:
            print(dt)
    """

    def __init__(self, freq, dtstart=None, interval=1, count=None, until=None, byweekday=None):
        if dtstart is None:
            dtstart = datetime.datetime.now(tz.UTC)
        self.freq = freq
        self.dtstart = dtstart
        self.interval = interval
        self.count = count
        self.until = until
        if byweekday is not None:
            if isinstance(byweekday, (list, tuple)):
                self.byweekday = [self._normalize_weekday(wd) for wd in byweekday]
            else:
                self.byweekday = [self._normalize_weekday(byweekday)]
        else:
            self.byweekday = None
        self._generated = 0
        self._current = None

    def _normalize_weekday(self, wd):
        # Accept _Weekday or int (0=MO)
        if isinstance(wd, _Weekday):
            return wd.weekday
        elif isinstance(wd, int):
            if 0 <= wd <= 6:
                return wd
            else:
                raise ValueError("Weekday integer must be in 0..6")
        else:
            raise TypeError("byweekday must be _Weekday or int")

    def __iter__(self):
        self._generated = 0
        self._current = self.dtstart
        # If byweekday is set and dtstart weekday not in byweekday, advance to next valid
        if self.byweekday is not None:
            if self._current.weekday() not in self.byweekday:
                self._current = self._next_valid(self._current)
        return self

    def __next__(self):
        if self.count is not None and self._generated >= self.count:
            raise StopIteration
        if self._current is None:
            self._current = self.dtstart
        else:
            if self._generated > 0:
                self._current = self._increment(self._current)
                # If byweekday is set, advance until valid weekday
                if self.byweekday is not None:
                    while self._current.weekday() not in self.byweekday:
                        self._current = self._increment(self._current)
        if self.until is not None and self._current > self.until:
            raise StopIteration
        self._generated += 1
        return self._current

    def _increment(self, dt):
        if self.freq == DAILY:
            return dt + datetime.timedelta(days=self.interval)
        elif self.freq == WEEKLY:
            return dt + datetime.timedelta(weeks=self.interval)
        else:
            raise ValueError("Unsupported frequency")

    def _next_valid(self, dt):
        # Advance dt until weekday in byweekday
        dt2 = dt
        while dt2.weekday() not in self.byweekday:
            dt2 += datetime.timedelta(days=1)
        return dt2