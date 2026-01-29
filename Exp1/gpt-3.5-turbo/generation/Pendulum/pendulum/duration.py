from datetime import timedelta as _timedelta

class Duration:
    __slots__ = ("_timedelta",)

    def __init__(self, days=0, seconds=0, microseconds=0):
        self._timedelta = _timedelta(days=days, seconds=seconds, microseconds=microseconds)

    @classmethod
    def from_timedelta(cls, td):
        obj = cls.__new__(cls)
        obj._timedelta = td
        return obj

    def total_seconds(self):
        return self._timedelta.total_seconds()

    def __repr__(self):
        return f"<Duration [{self._timedelta}]>"

    def __str__(self):
        return str(self._timedelta)

    def __add__(self, other):
        if isinstance(other, Duration):
            return Duration.from_timedelta(self._timedelta + other._timedelta)
        raise TypeError("Can only add Duration to Duration")

    def __sub__(self, other):
        if isinstance(other, Duration):
            return Duration.from_timedelta(self._timedelta - other._timedelta)
        raise TypeError("Can only subtract Duration from Duration")

    def __neg__(self):
        return Duration.from_timedelta(-self._timedelta)

    def __eq__(self, other):
        if not isinstance(other, Duration):
            return False
        return self._timedelta == other._timedelta


def duration(days=0, hours=0, minutes=0, seconds=0, microseconds=0):
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return Duration(days=days, seconds=total_seconds, microseconds=microseconds)