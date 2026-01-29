import datetime as _dt

class Duration:
    """
    Minimal duration compatible with basic Pendulum usage.
    Wraps a datetime.timedelta, supports arithmetic and humanization helpers.
    """

    __slots__ = ("_tdelta",)

    def __init__(self, days: int = 0, seconds: int = 0, microseconds: int = 0):
        self._tdelta = _dt.timedelta(days=days, seconds=seconds, microseconds=microseconds)

    @classmethod
    def from_timedelta(cls, td: _dt.timedelta) -> "Duration":
        obj = cls.__new__(cls)
        obj._tdelta = td
        return obj

    # arithmetic

    def __add__(self, other):
        if isinstance(other, Duration):
            return Duration.from_timedelta(self._tdelta + other._tdelta)
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Duration):
            return Duration.from_timedelta(self._tdelta - other._tdelta)
        return NotImplemented

    def __neg__(self):
        return Duration.from_timedelta(-self._tdelta)

    def __abs__(self):
        # timedelta has no abs, emulate
        if self._tdelta >= _dt.timedelta(0):
            return Duration.from_timedelta(self._tdelta)
        return Duration.from_timedelta(-self._tdelta)

    # comparisons (based on timedelta)

    def __eq__(self, other):
        if isinstance(other, Duration):
            return self._tdelta == other._tdelta
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Duration):
            return self._tdelta < other._tdelta
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Duration):
            return self._tdelta <= other._tdelta
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Duration):
            return self._tdelta > other._tdelta
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Duration):
            return self._tdelta >= other._tdelta
        return NotImplemented

    # representation

    def __repr__(self):
        return f"Duration({self._tdelta})"

    # helpers

    def total_seconds(self) -> float:
        return self._tdelta.total_seconds()

    def in_seconds(self) -> int:
        return int(self.total_seconds())

    def in_minutes(self) -> int:
        return int(self.total_seconds() // 60)

    def in_hours(self) -> int:
        return int(self.total_seconds() // 3600)

    def in_days(self) -> int:
        return int(self.total_seconds() // 86400)

    @property
    def as_timedelta(self) -> _dt.timedelta:
        return self._tdelta