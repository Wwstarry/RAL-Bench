import datetime as _datetime

class Duration:
    def __init__(self, days=0, seconds=0, microseconds=0,
                 milliseconds=0, minutes=0, hours=0, weeks=0):
        total = microseconds
        total += milliseconds * 1000
        total += (seconds + minutes * 60 + hours * 3600 + weeks * 7 * 24 * 3600 + days * 24 * 3600) * 1000000
        self._microseconds = total

    def __repr__(self):
        return f"<Duration [{self.as_timedelta()}]>"

    def as_timedelta(self):
        return _datetime.timedelta(microseconds=self._microseconds)

    def total_seconds(self):
        return self._microseconds / 1_000_000

    def __add__(self, other):
        from .datetime import DateTime
        if isinstance(other, Duration):
            return Duration(microseconds=self._microseconds + other._microseconds)
        elif isinstance(other, DateTime):
            return other.add(self)
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

def duration(days=0, seconds=0, microseconds=0,
             milliseconds=0, minutes=0, hours=0, weeks=0):
    return Duration(days, seconds, microseconds,
                    milliseconds, minutes, hours, weeks)