import datetime as dt

class Duration(dt.timedelta):

    def __new__(cls, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
        seconds += minutes * 60 + hours * 3600
        microseconds += milliseconds * 1000
        return super().__new__(cls, days=days, seconds=seconds, microseconds=microseconds, weeks=weeks)

    def __add__(self, other):
        if isinstance(other, Duration):
            return Duration(seconds=self.total_seconds() + other.total_seconds())
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Duration):
            return Duration(seconds=self.total_seconds() - other.total_seconds())
        return NotImplemented

    def __neg__(self):
        return Duration(seconds=-self.total_seconds())

    def in_seconds(self):
        return self.total_seconds()

    def in_words(self):
        # Simplified version - full implementation would be more complex
        parts = []
        if self.days > 0:
            parts.append(f"{self.days} days")
        if self.seconds > 0:
            parts.append(f"{self.seconds} seconds")
        if self.microseconds > 0:
            parts.append(f"{self.microseconds} microseconds")
        return ' '.join(parts)