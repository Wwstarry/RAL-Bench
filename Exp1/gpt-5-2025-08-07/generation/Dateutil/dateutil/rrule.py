from datetime import datetime, timedelta, timezone

# Frequency constants compatible with python-dateutil
YEARLY = 0
MONTHLY = 1
WEEKLY = 2
DAILY = 3
HOURLY = 4
MINUTELY = 5
SECONDLY = 6


class weekday:
    """
    Weekday specifier used in byweekday for rrule.
    """
    def __init__(self, weekday, n=None):
        self.weekday = int(weekday) % 7
        self.n = n

    def __call__(self, n):
        return weekday(self.weekday, n)

    def __repr__(self):
        names = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
        if self.n is None:
            return names[self.weekday]
        else:
            return "%s(%d)" % (names[self.weekday], self.n)

    def __eq__(self, other):
        if isinstance(other, weekday):
            return self.weekday == other.weekday and self.n == other.n
        return self.weekday == int(other)


MO = weekday(0)
TU = weekday(1)
WE = weekday(2)
TH = weekday(3)
FR = weekday(4)
SA = weekday(5)
SU = weekday(6)


def _to_weekday_set(byweekday):
    if byweekday is None:
        return None
    if isinstance(byweekday, weekday):
        return {byweekday.weekday}
    if isinstance(byweekday, int):
        return {byweekday % 7}
    try:
        s = set()
        for w in byweekday:
            if isinstance(w, weekday):
                s.add(w.weekday)
            else:
                s.add(int(w) % 7)
        return s
    except TypeError:
        # Not iterable, fallback
        return {int(byweekday) % 7}


class rrule:
    """
    Simplified recurrence rule generator with compatibility to python-dateutil rrule
    for DAILY and WEEKLY frequencies and byweekday filtering.

    Parameters:
    - freq: DAILY or WEEKLY (basic support)
    - interval: step size (default 1)
    - dtstart: starting datetime (required)
    - count: number of occurrences to generate (optional)
    - until: last occurrence inclusive (optional)
    - byweekday: weekdays to include (optional)
    - byhour, byminute, bysecond: time-of-day filters (optional)
    - bymonth, bymonthday: optional filters (limited support)
    """
    def __init__(self, freq, interval=1, dtstart=None, count=None, until=None,
                 byweekday=None, byhour=None, byminute=None, bysecond=None,
                 bymonth=None, bymonthday=None):
        if dtstart is None:
            raise ValueError("dtstart is required")
        if not isinstance(dtstart, datetime):
            raise TypeError("dtstart must be a datetime")

        if freq not in (DAILY, WEEKLY, MONTHLY, YEARLY, HOURLY, MINUTELY, SECONDLY):
            raise ValueError("Unsupported frequency")

        self.freq = freq
        self.interval = int(interval) if interval is not None else 1
        if self.interval <= 0:
            raise ValueError("interval must be >= 1")
        self.dtstart = dtstart
        self.count = count
        self.until = until
        self.byweekday = _to_weekday_set(byweekday)
        self.bymonth = set(bymonth) if bymonth is not None else None
        self.bymonthday = set(bymonthday) if bymonthday is not None else None

        def _norm_seq(x):
            if x is None:
                return None
            if isinstance(x, int):
                return [x]
            try:
                return [int(v) for v in x]
            except TypeError:
                return [int(x)]

        self.byhour = _norm_seq(byhour)
        self.byminute = _norm_seq(byminute)
        self.bysecond = _norm_seq(bysecond)

        # Build time-of-day combinations
        self._times = []
        if self.byhour is None and self.byminute is None and self.bysecond is None:
            self._times = [(dtstart.hour, dtstart.minute, dtstart.second, dtstart.microsecond)]
        else:
            hours = self.byhour if self.byhour is not None else [dtstart.hour]
            minutes = self.byminute if self.byminute is not None else [dtstart.minute]
            seconds = self.bysecond if self.bysecond is not None else [dtstart.second]
            microsecond = dtstart.microsecond
            for h in hours:
                for m in minutes:
                    for s in seconds:
                        self._times.append((h, m, s, microsecond))

    def __iter__(self):
        return self._iter()

    def _iter(self):
        yielded = 0
        current_date = self.dtstart.date()

        # Helper: check until
        def not_after_until(dt):
            if self.until is None:
                return True
            if dt.tzinfo and isinstance(self.until, datetime) and self.until.tzinfo:
                return dt.astimezone(timezone.utc) <= self.until.astimezone(timezone.utc)
            return dt <= self.until

        # Determine freq step
        if self.freq in (DAILY, WEEKLY):
            # Scan forward day by day
            day = self.dtstart
            # If dtstart matches, include it
            while True:
                # Apply filters to this day
                day_date = day.date()
                # bymonth filter
                if self.bymonth is not None and day.month not in self.bymonth:
                    pass  # skip by not yielding times
                else:
                    # bymonthday filter
                    if self.bymonthday is not None and day.day not in self.bymonthday:
                        pass
                    else:
                        # interval logic
                        include_day = True
                        if self.freq == DAILY:
                            delta_days = (day_date - self.dtstart.date()).days
                            include_day = (delta_days % self.interval == 0)
                        elif self.freq == WEEKLY:
                            delta_days = (day_date - self.dtstart.date()).days
                            weeks = delta_days // 7
                            include_day = (weeks % self.interval == 0)
                        # byweekday filter
                        if include_day:
                            if self.byweekday is None:
                                # For WEEKLY default: only the same weekday as dtstart
                                if self.freq == WEEKLY:
                                    include_day = (day.weekday() == self.dtstart.weekday())
                                else:
                                    include_day = True
                            else:
                                include_day = (day.weekday() in self.byweekday)

                        if include_day:
                            for (h, m, s, us) in self._times:
                                occurrence = day.replace(hour=h, minute=m, second=s, microsecond=us)
                                if not not_after_until(occurrence):
                                    return
                                yield occurrence
                                yielded += 1
                                if self.count is not None and yielded >= self.count:
                                    return

                # Advance to next day
                day = day + timedelta(days=1)
                # Optimization: if until is defined and day at midnight already exceeds, stop
                if self.until is not None:
                    # Compare dates to avoid time-of-day effects
                    if isinstance(self.until, datetime):
                        until_date = self.until.date()
                    else:
                        until_date = self.until
                    if day.date() > until_date:
                        return

        elif self.freq == MONTHLY:
            # Basic monthly: each interval months, same day as dtstart unless filtered by bymonthday/byweekday (ignored here)
            day = self.dtstart
            while True:
                if self.bymonth is None or day.month in self.bymonth:
                    if self.bymonthday is None or day.day in self.bymonthday:
                        for (h, m, s, us) in self._times:
                            occ = day.replace(hour=h, minute=m, second=s, microsecond=us)
                            if not not_after_until(occ):
                                return
                            yield occ
                            yielded += 1
                            if self.count is not None and yielded >= self.count:
                                return
                # advance months
                months_total = day.month - 1 + self.interval
                new_year = day.year + months_total // 12
                new_month = months_total % 12 + 1
                # clamp day to last of month
                last_day = calendar.monthrange(new_year, new_month)[1]
                new_dom = min(day.day, last_day)
                day = day.replace(year=new_year, month=new_month, day=new_dom)

        else:
            # For other frequencies, implement a minimal stepping
            step = None
            if self.freq == YEARLY:
                step = "year"
            elif self.freq == HOURLY:
                delta = timedelta(hours=self.interval)
            elif self.freq == MINUTELY:
                delta = timedelta(minutes=self.interval)
            elif self.freq == SECONDLY:
                delta = timedelta(seconds=self.interval)

            if step == "year":
                day = self.dtstart
                while True:
                    for (h, m, s, us) in self._times:
                        occ = day.replace(hour=h, minute=m, second=s, microsecond=us)
                        if not not_after_until(occ):
                            return
                        yield occ
                        yielded += 1
                        if self.count is not None and yielded >= self.count:
                            return
                    day = day.replace(year=day.year + self.interval)
            else:
                # Hourly/minutely/secondly
                current = self.dtstart
                while True:
                    if self.bymonth is None or current.month in self.bymonth:
                        if self.bymonthday is None or current.day in self.bymonthday:
                            if self.byweekday is None or current.weekday() in self.byweekday:
                                if not not_after_until(current):
                                    return
                                yield current
                                yielded += 1
                                if self.count is not None and yielded >= self.count:
                                    return
                    current = current + delta

    def __repr__(self):
        return "rrule(freq=%r, interval=%r, dtstart=%r, count=%r, until=%r)" % (self.freq, self.interval, self.dtstart, self.count, self.until)


def rrule(freq, interval=1, dtstart=None, count=None, until=None,
          byweekday=None, byhour=None, byminute=None, bysecond=None,
          bymonth=None, bymonthday=None):
    return rrule_class(freq, interval=interval, dtstart=dtstart, count=count, until=until,
                       byweekday=byweekday, byhour=byhour, byminute=byminute, bysecond=bysecond,
                       bymonth=bymonth, bymonthday=bymonthday)


# Alias to match python-dateutil API where rrule is both function and class; we provide rrule_class for clarity
rrule_class = rrule