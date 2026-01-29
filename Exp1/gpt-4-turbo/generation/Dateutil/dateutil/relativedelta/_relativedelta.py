from datetime import datetime, timedelta, date

class relativedelta:
    def __init__(
        self,
        dt1=None,
        dt2=None,
        years=0,
        months=0,
        days=0,
        hours=0,
        minutes=0,
        seconds=0,
        microseconds=0,
        leapdays=0,
        weeks=0,
        weekday=None,
    ):
        self.years = years
        self.months = months
        self.days = days + weeks * 7
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.microseconds = microseconds
        self.leapdays = leapdays
        self.weekday = weekday

        if dt1 is not None and dt2 is not None:
            self._from_diff(dt1, dt2)

    def _from_diff(self, dt1, dt2):
        # Compute difference in years, months, days, etc.
        # Only for date or datetime objects
        if isinstance(dt1, datetime) and isinstance(dt2, datetime):
            d1 = dt1
            d2 = dt2
        elif isinstance(dt1, date) and isinstance(dt2, date):
            d1 = datetime(dt1.year, dt1.month, dt1.day)
            d2 = datetime(dt2.year, dt2.month, dt2.day)
        else:
            raise TypeError("relativedelta: dt1 and dt2 must be date or datetime")
        # Years and months
        years = d2.year - d1.year
        months = d2.month - d1.month
        days = d2.day - d1.day
        hours = d2.hour - d1.hour
        minutes = d2.minute - d1.minute
        seconds = d2.second - d1.second
        microseconds = d2.microsecond - d1.microsecond
        # Normalize months
        if months < 0:
            years -= 1
            months += 12
        self.years = years
        self.months = months
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.microseconds = microseconds

    def __add__(self, other):
        if isinstance(other, (datetime, date)):
            return self._apply(other, 1)
        raise TypeError("relativedelta can only be added to date or datetime")

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, (datetime, date)):
            return self._apply(other, -1)
        raise TypeError("relativedelta can only be subtracted from date or datetime")

    def __rsub__(self, other):
        return self.__sub__(other)

    def _apply(self, dt, sign):
        # Apply years and months
        year = dt.year + sign * self.years
        month = dt.month + sign * self.months
        while month > 12:
            year += 1
            month -= 12
        while month < 1:
            year -= 1
            month += 12
        # Clamp day to last day of month
        day = dt.day
        from calendar import monthrange
        last_day = monthrange(year, month)[1]
        if day > last_day:
            day = last_day
        # Apply days, hours, minutes, seconds, microseconds
        result = dt.replace(year=year, month=month, day=day)
        delta = timedelta(
            days=sign * self.days + sign * self.leapdays,
            hours=sign * self.hours,
            minutes=sign * self.minutes,
            seconds=sign * self.seconds,
            microseconds=sign * self.microseconds,
        )
        result = result + delta
        # Apply weekday if specified
        if self.weekday is not None:
            # weekday: (weekday, nth)
            weekday, nth = self.weekday
            # Find nth weekday in month
            from calendar import monthcalendar
            cal = monthcalendar(result.year, result.month)
            days = [week[weekday] for week in cal if week[weekday] != 0]
            if nth > 0:
                day = days[nth - 1]
            else:
                day = days[nth]
            result = result.replace(day=day)
        return result

    def __repr__(self):
        args = []
        for k in ["years", "months", "days", "hours", "minutes", "seconds", "microseconds", "leapdays"]:
            v = getattr(self, k)
            if v:
                args.append(f"{k}={v}")
        if self.weekday:
            args.append(f"weekday={self.weekday}")
        return f"relativedelta({', '.join(args)})"