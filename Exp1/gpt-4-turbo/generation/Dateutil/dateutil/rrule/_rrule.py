from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

YEARLY = 0
MONTHLY = 1
WEEKLY = 2
DAILY = 3
HOURLY = 4
MINUTELY = 5
SECONDLY = 6

class weekday:
    def __init__(self, n, nth=None):
        self.n = n
        self.nth = nth

    def __call__(self, nth):
        return weekday(self.n, nth)

    def __eq__(self, other):
        return isinstance(other, weekday) and self.n == other.n and self.nth == other.nth

    def __repr__(self):
        if self.nth is not None:
            return f"weekday({self.n}, {self.nth})"
        return f"weekday({self.n})"

MO = weekday(0)
TU = weekday(1)
WE = weekday(2)
TH = weekday(3)
FR = weekday(4)
SA = weekday(5)
SU = weekday(6)

FREQ_MAP = {
    YEARLY: "years",
    MONTHLY: "months",
    WEEKLY: "weeks",
    DAILY: "days",
    HOURLY: "hours",
    MINUTELY: "minutes",
    SECONDLY: "seconds",
}

class rrule:
    def __init__(
        self,
        freq,
        dtstart=None,
        interval=1,
        wkst=MO,
        count=None,
        until=None,
        bysetpos=None,
        bymonth=None,
        bymonthday=None,
        byyearday=None,
        byweekno=None,
        byweekday=None,
        byhour=None,
        byminute=None,
        bysecond=None,
        cache=False,
    ):
        self.freq = freq
        self.dtstart = dtstart or datetime.now()
        self.interval = interval
        self.count = count
        self.until = until
        self.bysetpos = bysetpos
        self.bymonth = bymonth
        self.bymonthday = bymonthday
        self.byyearday = byyearday
        self.byweekno = byweekno
        self.byweekday = byweekday
        self.byhour = byhour
        self.byminute = byminute
        self.bysecond = bysecond
        self.wkst = wkst
        self.cache = cache

    def __iter__(self):
        return self._iter()

    def _iter(self):
        dt = self.dtstart
        freq = self.freq
        interval = self.interval
        count = self.count
        until = self.until
        byweekday = self.byweekday
        yielded = 0
        while True:
            # Filtering byweekday
            if byweekday is not None:
                if isinstance(byweekday, (list, tuple)):
                    weekdays = [w.n for w in byweekday]
                else:
                    weekdays = [byweekday.n]
                if dt.weekday() not in weekdays:
                    dt = self._advance(dt, freq, interval)
                    continue
            # Filtering bymonth
            if self.bymonth is not None:
                if isinstance(self.bymonth, (list, tuple)):
                    months = self.bymonth
                else:
                    months = [self.bymonth]
                if dt.month not in months:
                    dt = self._advance(dt, freq, interval)
                    continue
            # Filtering bymonthday
            if self.bymonthday is not None:
                if isinstance(self.bymonthday, (list, tuple)):
                    monthdays = self.bymonthday
                else:
                    monthdays = [self.bymonthday]
                if dt.day not in monthdays:
                    dt = self._advance(dt, freq, interval)
                    continue
            # Filtering byhour
            if self.byhour is not None:
                if isinstance(self.byhour, (list, tuple)):
                    hours = self.byhour
                else:
                    hours = [self.byhour]
                if dt.hour not in hours:
                    dt = self._advance(dt, freq, interval)
                    continue
            # Filtering byminute
            if self.byminute is not None:
                if isinstance(self.byminute, (list, tuple)):
                    minutes = self.byminute
                else:
                    minutes = [self.byminute]
                if dt.minute not in minutes:
                    dt = self._advance(dt, freq, interval)
                    continue
            # Filtering bysecond
            if self.bysecond is not None:
                if isinstance(self.bysecond, (list, tuple)):
                    seconds = self.bysecond
                else:
                    seconds = [self.bysecond]
                if dt.second not in seconds:
                    dt = self._advance(dt, freq, interval)
                    continue
            # Filtering bysetpos (not implemented)
            # Filtering byyearday, byweekno (not implemented)
            # Filtering until
            if until is not None and dt > until:
                break
            yield dt
            yielded += 1
            if count is not None and yielded >= count:
                break
            dt = self._advance(dt, freq, interval)

    def _advance(self, dt, freq, interval):
        if freq == YEARLY:
            return dt + relativedelta(years=interval)
        elif freq == MONTHLY:
            return dt + relativedelta(months=interval)
        elif freq == WEEKLY:
            return dt + relativedelta(weeks=interval)
        elif freq == DAILY:
            return dt + relativedelta(days=interval)
        elif freq == HOURLY:
            return dt + relativedelta(hours=interval)
        elif freq == MINUTELY:
            return dt + relativedelta(minutes=interval)
        elif freq == SECONDLY:
            return dt + relativedelta(seconds=interval)
        else:
            raise ValueError("Unknown frequency")