import datetime as _dt

class Duration(_dt.timedelta):
    """
    Pendulum Duration class, inheriting from datetime.timedelta.
    """
    def __new__(cls, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0, years=0, months=0):
        # Approximate years and months to days for timedelta compatibility
        # Note: Real pendulum stores these separately for precise arithmetic,
        # but for a lightweight compatible version, we normalize.
        total_days = days + (weeks * 7) + (years * 365) + (months * 30)
        return super().__new__(cls, days=total_days, seconds=seconds, microseconds=microseconds, 
                               milliseconds=milliseconds, minutes=minutes, hours=hours)

    @property
    def total_minutes(self):
        return self.total_seconds() / 60

    @property
    def total_hours(self):
        return self.total_seconds() / 3600

    @property
    def total_days(self):
        return self.total_seconds() / 86400

    @property
    def total_weeks(self):
        return self.total_days / 7

    def in_words(self, locale=None):
        """
        Simplified human readable duration.
        """
        seconds = abs(int(self.total_seconds()))
        if seconds < 60:
            return f"{seconds} second{'s' if seconds != 1 else ''}"
        
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
            
        hours = minutes // 60
        if hours < 24:
            return f"{hours} hour{'s' if hours != 1 else ''}"
            
        days = hours // 24
        return f"{days} day{'s' if days != 1 else ''}"

    def __iter__(self):
        # Pendulum durations are iterable (days, seconds, microseconds)
        yield self.days
        yield self.seconds
        yield self.microseconds