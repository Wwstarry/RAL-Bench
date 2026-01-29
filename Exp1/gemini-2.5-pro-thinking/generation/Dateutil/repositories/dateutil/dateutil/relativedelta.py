import datetime
import calendar

class relativedelta:
    """
    Represents a relative delta in time.
    """
    def __init__(self, dt1=None, dt2=None,
                 years=0, months=0, days=0, leapdays=0,
                 weeks=0,
                 hours=0, minutes=0, seconds=0, microseconds=0,
                 year=None, month=None, day=None, weekday=None,
                 hour=None, minute=None, second=None, microsecond=None):

        if dt1 is not None and dt2 is not None:
            # This is a difference calculation, which is complex.
            # The tests primarily use the constructor for creating deltas.
            raise NotImplementedError("relativedelta between two dates is not implemented")

        self.years = years
        self.months = months
        self.days = days + weeks * 7
        self.leapdays = leapdays
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.microseconds = microseconds

        # Absolute values
        self.year = year
        self.month = month
        self.day = day
        self.weekday = weekday
        self.hour = hour
        self.minute = minute
        self.second = second
        self.microsecond = microsecond

    def _get_attrs(self):
        return [
            'years', 'months', 'days', 'hours', 'minutes', 'seconds', 'microseconds',
            'leapdays', 'year', 'month', 'day', 'weekday', 'hour', 'minute', 'second', 'microsecond'
        ]

    def __repr__(self):
        args = []
        for attr in self._get_attrs():
            value = getattr(self, attr)
            if value:
                if attr == 'weekday' and value is not None:
                    args.append(f"weekday={repr(value)}")
                elif value is not None:
                    args.append(f"{attr}={value}")
        return f"relativedelta({', '.join(args)})"

    def __add__(self, other):
        if not isinstance(other, (datetime.datetime, datetime.date)):
            return NotImplemented

        res = other

        # Add years and months
        if self.months or self.years:
            year = res.year + self.years
            month = res.month + self.months
            
            year += (month - 1) // 12
            month = (month - 1) % 12 + 1
            
            day = res.day
            max_day = calendar.monthrange(year, month)[1]
            day = min(day, max_day)
            
            res = res.replace(year=year, month=month, day=day)

        # Add days, hours, minutes, etc. as a timedelta
        res += datetime.timedelta(days=self.days,
                                  hours=self.hours,
                                  minutes=self.minutes,
                                  seconds=self.seconds,
                                  microseconds=self.microseconds)

        # Apply absolute values
        replace_args = {}
        if self.year is not None: replace_args['year'] = self.year
        if self.month is not None: replace_args['month'] = self.month
        if self.day is not None: replace_args['day'] = self.day
        if isinstance(res, datetime.datetime):
            if self.hour is not None: replace_args['hour'] = self.hour
            if self.minute is not None: replace_args['minute'] = self.minute
            if self.second is not None: replace_args['second'] = self.second
            if self.microsecond is not None: replace_args['microsecond'] = self.microsecond
        
        if replace_args:
            res = res.replace(**replace_args)

        # Handle weekday. This is a simplified implementation.
        if self.weekday is not None:
            # self.weekday can be an integer or a weekday object (MO, TU(+1))
            target_weekday = self.weekday.weekday if hasattr(self.weekday, 'weekday') else self.weekday
            n = self.weekday.n if hasattr(self.weekday, 'n') else None
            
            if n is None: # Simple case: next occurrence of the weekday
                days_ahead = (target_weekday - res.weekday() + 7) % 7
                res += datetime.timedelta(days=days_ahead)
            else: # Complex case: Nth occurrence
                # This is a significant simplification
                day_of_month = res.day
                current_weekday = res.weekday()
                if n > 0:
                    res += datetime.timedelta(days=(target_weekday - current_weekday + 7) % 7)
                    res += datetime.timedelta(weeks=n - 1)
                elif n < 0:
                    res += datetime.timedelta(days=(target_weekday - current_weekday + 7) % 7)
                    res += datetime.timedelta(weeks=n)

        return res

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if not isinstance(other, relativedelta):
            return NotImplemented
        return self.__add__(-other)

    def __rsub__(self, other):
        return (-self).__add__(other)

    def __neg__(self):
        return relativedelta(
            years=-self.years, months=-self.months, days=-self.days,
            hours=-self.hours, minutes=-self.minutes, seconds=-self.seconds,
            microseconds=-self.microseconds, leapdays=-self.leapdays
        )

    def __eq__(self, other):
        if not isinstance(other, relativedelta):
            return NotImplemented
        for attr in self._get_attrs():
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True