import datetime

DAILY = "DAILY"
WEEKLY = "WEEKLY"
MO, TU, WE, TH, FR, SA, SU = range(7)

class rrule:
    def __init__(self, freq, dtstart=None, interval=1, count=None, byweekday=None):
        self.freq = freq
        self.dtstart = dtstart or datetime.datetime.now()
        self.interval = interval
        self.count = count
        self.byweekday = byweekday

    def __iter__(self):
        current = self.dtstart
        occurrences = 0

        while self.count is None or occurrences < self.count:
            if self.byweekday is None or current.weekday() in self.byweekday:
                yield current
                occurrences += 1

            if self.freq == DAILY:
                current += datetime.timedelta(days=self.interval)
            elif self.freq == WEEKLY:
                current += datetime.timedelta(weeks=self.interval)
            else:
                raise ValueError("Unsupported frequency: {}".format(self.freq))