"""
Extremely trimmed-down recurrence rule implementation inspired by
`dateutil.rrule`.  Only daily and weekly rules as well as ``byweekday`` filters
and ``interval``, ``count`` & ``until`` limits are supported.  This satisfies
the limited scenarios used by the test-suite.
"""
from __future__ import annotations

import datetime as _dt
from typing import Iterable, Iterator, List, Optional, Sequence, Union

# Frequency constants (match values used by python-dateutil)
YEARLY, MONTHLY, WEEKLY, DAILY, HOURLY, MINUTELY, SECONDLY = range(7)

# Weekday helper ------------------------------------------------------------


class weekday:
    __slots__ = ("_wkday",)

    def __init__(self, n: int):
        self._wkday = int(n) % 7

    def __eq__(self, other):
        if isinstance(other, weekday):
            return self._wkday == other._wkday
        if isinstance(other, int):
            return self._wkday == other % 7
        return NotImplemented

    def __hash__(self):
        return hash(self._wkday)

    def __int__(self):
        return self._wkday

    def __repr__(self):
        names = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
        return names[self._wkday]


# Predefined weekday instances
MO, TU, WE, TH, FR, SA, SU = [weekday(i) for i in range(7)]

__all__ = [
    "rrule",
    "MO",
    "TU",
    "WE",
    "TH",
    "FR",
    "SA",
    "SU",
    "YEARLY",
    "MONTHLY",
    "WEEKLY",
    "DAILY",
    "HOURLY",
    "MINUTELY",
    "SECONDLY",
]


class rrule:
    """
    Rudimentary recurrence rule iterator that supports *freq* of ``DAILY`` or
    ``WEEKLY`` with optional *interval*, *count*, *until* and *byweekday*.
    """

    def __init__(
        self,
        freq: int,
        dtstart: _dt.datetime,
        interval: int = 1,
        count: Optional[int] = None,
        until: Optional[_dt.datetime] = None,
        byweekday: Optional[
            Union[int, weekday, Sequence[Union[int, weekday]]]
        ] = None,
    ):
        if freq not in (DAILY, WEEKLY):
            raise NotImplementedError("Only DAILY and WEEKLY are implemented")

        if dtstart.tzinfo is not None and until is not None and until.tzinfo is None:
            # make until timezone aware if dtstart is aware
            until = until.replace(tzinfo=dtstart.tzinfo)

        self.freq = freq
        self.dtstart = dtstart
        self.interval = max(1, int(interval))
        self.count = count
        self.until = until
        self.byweekday = self._normalize_byweekday(byweekday)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_byweekday(
        bw: Optional[Union[int, weekday, Sequence[Union[int, weekday]]]]
    ) -> Optional[List[int]]:
        if bw is None:
            return None
        if isinstance(bw, (int, weekday)):
            return [int(bw)]
        return [int(x) for x in bw]

    # ------------------------------------------------------------------
    # Iterator protocol
    # ------------------------------------------------------------------
    def __iter__(self) -> Iterator[_dt.datetime]:
        yielded = 0
        current = self.dtstart

        while True:
            if self.until is not None and current > self.until:
                break

            if self._include(current):
                yielded += 1
                yield current
                if self.count is not None and yielded >= self.count:
                    break

            current = self._next(current)

    # ------------------------------------------------------------------
    # Internal step helpers
    # ------------------------------------------------------------------
    def _include(self, dt: _dt.datetime) -> bool:
        if self.byweekday is not None and dt.weekday() not in self.byweekday:
            return False
        return True

    def _next(self, dt: _dt.datetime) -> _dt.datetime:
        if self.freq == DAILY:
            return dt + _dt.timedelta(days=self.interval)
        elif self.freq == WEEKLY:
            # Step by a single day until we find the next date that starts a
            # new ``interval`` sized week block or matches filtering rules.
            candidate = dt + _dt.timedelta(days=1)
            while True:
                weeks_since_start = (
                    candidate - self.dtstart.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                ).days // 7
                if weeks_since_start % self.interval == 0:
                    return candidate
                candidate += _dt.timedelta(days=1)
        else:
            # Not reachable due to constructor guard
            raise AssertionError("Unsupported frequency")


# Convenience factory mirroring python-dateutil signature -------------------


def _rrule(
    freq: int,
    dtstart: _dt.datetime,
    interval: int = 1,
    count: Optional[int] = None,
    until: Optional[_dt.datetime] = None,
    byweekday: Optional[
        Union[int, weekday, Iterable[Union[int, weekday]]]
    ] = None,
):
    return rrule(freq, dtstart, interval=interval, count=count, until=until, byweekday=byweekday)


# Expose factory directly under the module name to match API
rrule = _rrule  # type: ignore