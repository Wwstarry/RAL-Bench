from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Iterator, Optional, Sequence, Union

# Frequency constants
YEARLY = 0
MONTHLY = 1
WEEKLY = 2
DAILY = 3
HOURLY = 4
MINUTELY = 5
SECONDLY = 6

__all__ = [
    "rrule",
    "rruleset",
    "DAILY",
    "WEEKLY",
    "MONTHLY",
    "YEARLY",
    "HOURLY",
    "MINUTELY",
    "SECONDLY",
    "MO",
    "TU",
    "WE",
    "TH",
    "FR",
    "SA",
    "SU",
]


@dataclass(frozen=True)
class weekday:
    weekday: int  # 0=MO .. 6=SU

    def __call__(self, n: int):
        # Compatibility placeholder: dateutil allows MO(1), etc. Not needed for core tests.
        return self

    def __repr__(self):
        names = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
        return names[self.weekday]


MO = weekday(0)
TU = weekday(1)
WE = weekday(2)
TH = weekday(3)
FR = weekday(4)
SA = weekday(5)
SU = weekday(6)


def _coerce_byweekday(bw):
    if bw is None:
        return None
    if isinstance(bw, weekday):
        return [bw.weekday]
    if isinstance(bw, int):
        return [bw]
    out = []
    for x in bw:
        if isinstance(x, weekday):
            out.append(x.weekday)
        elif isinstance(x, int):
            out.append(x)
        else:
            raise TypeError("Invalid byweekday element")
    return out


class rrule(Iterable[datetime]):
    """
    Minimal rrule implementation supporting frequencies DAILY and WEEKLY,
    interval, count, until, dtstart, and byweekday filtering.
    """

    def __init__(
        self,
        freq: int,
        *,
        dtstart: Optional[datetime] = None,
        interval: int = 1,
        count: Optional[int] = None,
        until: Optional[datetime] = None,
        byweekday=None,
    ):
        if dtstart is None:
            dtstart = datetime.now()
        self._freq = int(freq)
        self._dtstart = dtstart
        self._interval = int(interval) if interval else 1
        self._count = count
        self._until = until
        self._byweekday = _coerce_byweekday(byweekday)

    def __iter__(self) -> Iterator[datetime]:
        yielded = 0
        current = self._dtstart

        if self._freq == DAILY:
            step = timedelta(days=self._interval)

            while True:
                if self._until is not None and current > self._until:
                    break
                if self._byweekday is None or current.weekday() in self._byweekday:
                    yield current
                    yielded += 1
                    if self._count is not None and yielded >= self._count:
                        break
                current = current + step

        elif self._freq == WEEKLY:
            # For weekly rules, dateutil steps by weeks but emits matching weekdays within each week.
            # We implement stable behavior:
            # - Determine the set of weekdays to emit; default is weekday(dtstart)
            # - For each week bucket starting at dtstart, emit occurrences >= dtstart in that week
            # - Preserve time/tzinfo from dtstart
            bwd = self._byweekday[:] if self._byweekday is not None else [self._dtstart.weekday()]
            bwd = sorted(set(bwd))

            week0 = self._dtstart
            # start of "week" anchored at dtstart's date, not calendar week.
            # Generate within each 7-day window [week0, week0+7).
            while True:
                # emit days in this window
                for wd in bwd:
                    # compute candidate by moving from week0 to that weekday within the window
                    delta = wd - week0.weekday()
                    cand = week0 + timedelta(days=delta)
                    # ensure in window:
                    if cand < week0:
                        cand += timedelta(days=7)
                    # ensure not before dtstart
                    if cand < self._dtstart:
                        continue
                    if self._until is not None and cand > self._until:
                        return
                    yield cand
                    yielded += 1
                    if self._count is not None and yielded >= self._count:
                        return
                week0 = week0 + timedelta(days=7 * self._interval)
                if self._until is not None and week0 > self._until:
                    return
        else:
            raise NotImplementedError("This minimal rrule supports DAILY and WEEKLY only")

    def __getitem__(self, item):
        # Support slicing / indexing minimally for tests.
        if isinstance(item, slice):
            start = item.start or 0
            stop = item.stop
            step = item.step or 1
            res = []
            for i, dt in enumerate(self):
                if i < start:
                    continue
                if stop is not None and i >= stop:
                    break
                if (i - start) % step == 0:
                    res.append(dt)
            return res
        if isinstance(item, int):
            if item < 0:
                raise IndexError("Negative indices not supported")
            for i, dt in enumerate(self):
                if i == item:
                    return dt
            raise IndexError("rrule index out of range")
        raise TypeError("Invalid index type")

    def between(self, after: datetime, before: datetime, inc: bool = False) -> list[datetime]:
        out = []
        for dt in self:
            if inc:
                if dt < after:
                    continue
                if dt > before:
                    break
            else:
                if dt <= after:
                    continue
                if dt >= before:
                    break
            out.append(dt)
        return out

    def __repr__(self):
        return (
            f"rrule(freq={self._freq}, dtstart={self._dtstart!r}, interval={self._interval}, "
            f"count={self._count!r}, until={self._until!r}, byweekday={self._byweekday!r})"
        )


class rruleset(Iterable[datetime]):
    """
    Minimal rruleset: supports adding rrules and iterating merged results.
    Only what is commonly used in tests.
    """

    def __init__(self):
        self._rrules: list[rrule] = []

    def rrule(self, rule: rrule):
        self._rrules.append(rule)
        return self

    def __iter__(self):
        # naive merge: generate all from each rule up to its count/until,
        # then sort and yield unique.
        items = []
        for r in self._rrules:
            items.extend(list(r))
        items.sort()
        last = object()
        for x in items:
            if last is object() or x != last:
                yield x
            last = x