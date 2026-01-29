"""
A small, pure-Python job scheduling library compatible with the core API of
the reference "schedule" project.

Exposes:
- schedule.every
- schedule.Job
- schedule.Scheduler

Supports:
- schedule.every(n).seconds / minutes / hours / days / weeks
- schedule.every().day.at("HH:MM" or "HH:MM:SS")
- schedule.every().monday (and other weekdays)
- Scheduler.run_pending(), Scheduler.run_all()
"""

from __future__ import annotations

import datetime as _datetime
import functools as _functools
import random as _random
from dataclasses import dataclass as _dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union

__all__ = ["every", "Job", "Scheduler"]


def _now() -> _datetime.datetime:
    # Important for test determinism: always resolve "now" at call sites
    # via datetime.datetime.now(), which can be monkeypatched.
    return _datetime.datetime.now()


def _is_naive(dt: _datetime.datetime) -> bool:
    return dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None


def _coerce_to_datetime(
    dt: Union[_datetime.datetime, _datetime.date],
    ref: Optional[_datetime.datetime] = None,
) -> _datetime.datetime:
    if isinstance(dt, _datetime.datetime):
        return dt
    if isinstance(dt, _datetime.date):
        if ref is None:
            ref = _now()
        return _datetime.datetime.combine(dt, ref.time())
    raise TypeError("Expected datetime or date")


def _parse_time_str(s: str) -> _datetime.time:
    # Accept "HH:MM" or "HH:MM:SS"
    parts = s.split(":")
    if len(parts) not in (2, 3):
        raise ValueError("Invalid time format, expected HH:MM or HH:MM:SS")
    try:
        h = int(parts[0])
        m = int(parts[1])
        sec = int(parts[2]) if len(parts) == 3 else 0
    except Exception as e:
        raise ValueError("Invalid time format") from e
    if not (0 <= h <= 23 and 0 <= m <= 59 and 0 <= sec <= 59):
        raise ValueError("Invalid time values")
    return _datetime.time(hour=h, minute=m, second=sec)


_WEEKDAYS: Dict[str, int] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


class CancelJob:
    """Return from a job function to unschedule it."""


class Scheduler:
    def __init__(self) -> None:
        self.jobs: List[Job] = []

    def every(self, interval: int = 1) -> "Job":
        job = Job(interval=interval, scheduler=self)
        return job

    def run_pending(self) -> None:
        now = _now()
        runnable = [job for job in self.jobs if job.should_run(now)]
        runnable.sort(key=lambda j: j.next_run or _datetime.datetime.max)
        for job in runnable:
            self._run_job(job)

    def run_all(self, delay_seconds: int = 0) -> None:
        # Run all jobs regardless of schedule; reschedule each afterwards.
        # delay_seconds exists for API compatibility; tests typically pass 0.
        for job in list(self.jobs):
            self._run_job(job)
            if delay_seconds:
                # Avoid importing time at module import; keep tests predictable.
                import time as _time

                _time.sleep(delay_seconds)

    def _run_job(self, job: "Job") -> None:
        ret = job.run()
        if ret is CancelJob or ret is CancelJob():
            self.cancel_job(job)

    def cancel_job(self, job: "Job") -> None:
        try:
            self.jobs.remove(job)
        except ValueError:
            pass

    def clear(self, tag: Optional[Union[str, Sequence[str]]] = None) -> None:
        if tag is None:
            self.jobs.clear()
            return
        if isinstance(tag, (list, tuple, set)):
            tags = set(tag)
        else:
            tags = {tag}
        self.jobs = [j for j in self.jobs if not (j.tags & tags)]

    def get_jobs(self, tag: Optional[str] = None) -> List["Job"]:
        if tag is None:
            return list(self.jobs)
        return [j for j in self.jobs if tag in j.tags]

    @property
    def next_run(self) -> Optional[_datetime.datetime]:
        if not self.jobs:
            return None
        nexts = [j.next_run for j in self.jobs if j.next_run is not None]
        return min(nexts) if nexts else None

    @property
    def idle_seconds(self) -> Optional[float]:
        nr = self.next_run
        if nr is None:
            return None
        return (nr - _now()).total_seconds()


class Job:
    """
    Represents a periodic job.
    """

    def __init__(self, interval: int, scheduler: Optional[Scheduler] = None) -> None:
        if interval is None:
            interval = 1
        if interval <= 0:
            raise ValueError("Interval must be a positive integer")
        self.interval: int = interval
        self.latest: Optional[int] = None  # when using .to()
        self.unit: Optional[str] = None  # seconds/minutes/hours/days/weeks
        self.at_time: Optional[_datetime.time] = None
        self.start_day: Optional[int] = None  # weekday index 0=Mon
        self.job_func: Optional[Callable[..., Any]] = None
        self.job_func_args: Tuple[Any, ...] = ()
        self.job_func_kwargs: Dict[str, Any] = {}
        self.last_run: Optional[_datetime.datetime] = None
        self.next_run: Optional[_datetime.datetime] = None
        self.scheduler: Optional[Scheduler] = scheduler
        self.tags: Set[str] = set()

    def __repr__(self) -> str:
        return (
            f"Job(interval={self.interval}, unit={self.unit}, "
            f"at_time={self.at_time}, start_day={self.start_day}, "
            f"next_run={self.next_run}, last_run={self.last_run})"
        )

    # --- unit properties ---
    @property
    def second(self) -> "Job":
        return self.seconds

    @property
    def seconds(self) -> "Job":
        self.unit = "seconds"
        return self

    @property
    def minute(self) -> "Job":
        return self.minutes

    @property
    def minutes(self) -> "Job":
        self.unit = "minutes"
        return self

    @property
    def hour(self) -> "Job":
        return self.hours

    @property
    def hours(self) -> "Job":
        self.unit = "hours"
        return self

    @property
    def day(self) -> "Job":
        return self.days

    @property
    def days(self) -> "Job":
        self.unit = "days"
        return self

    @property
    def week(self) -> "Job":
        return self.weeks

    @property
    def weeks(self) -> "Job":
        self.unit = "weeks"
        return self

    # --- weekdays ---
    @property
    def monday(self) -> "Job":
        self._set_weekday("monday")
        return self

    @property
    def tuesday(self) -> "Job":
        self._set_weekday("tuesday")
        return self

    @property
    def wednesday(self) -> "Job":
        self._set_weekday("wednesday")
        return self

    @property
    def thursday(self) -> "Job":
        self._set_weekday("thursday")
        return self

    @property
    def friday(self) -> "Job":
        self._set_weekday("friday")
        return self

    @property
    def saturday(self) -> "Job":
        self._set_weekday("saturday")
        return self

    @property
    def sunday(self) -> "Job":
        self._set_weekday("sunday")
        return self

    def _set_weekday(self, day: str) -> None:
        self.start_day = _WEEKDAYS[day]
        # Reference behavior: weekday scheduling implies weeks unit if not set.
        if self.unit is None:
            self.unit = "weeks"

    # --- configuration methods ---
    def at(self, time_str: str) -> "Job":
        # Allowed for daily/hourly/minutely jobs in reference; tests use .day.at()
        self.at_time = _parse_time_str(time_str)
        return self

    def to(self, latest: int) -> "Job":
        if latest < self.interval:
            raise ValueError("Latest must be >= interval")
        self.latest = latest
        return self

    def tag(self, *tags: str) -> "Job":
        for t in tags:
            if t is None:
                continue
            self.tags.add(str(t))
        return self

    def do(self, job_func: Callable[..., Any], *args: Any, **kwargs: Any) -> "Job":
        self.job_func = job_func
        self.job_func_args = args
        self.job_func_kwargs = kwargs
        # Register on scheduler
        if self.scheduler is not None and self not in self.scheduler.jobs:
            self.scheduler.jobs.append(self)
        self._schedule_next_run()
        return self

    # --- runtime ---
    def should_run(self, now: Optional[_datetime.datetime] = None) -> bool:
        if now is None:
            now = _now()
        if self.next_run is None:
            self._schedule_next_run(now)
        return self.next_run is not None and now >= self.next_run

    def run(self) -> Any:
        if self.job_func is None:
            return None
        now = _now()
        ret = self.job_func(*self.job_func_args, **self.job_func_kwargs)
        self.last_run = now
        self._schedule_next_run(now)
        return ret

    # --- scheduling calculations ---
    def _validate(self) -> None:
        if self.unit is None:
            raise ValueError("Time unit not set; use .seconds/.minutes/.hours/.days/.weeks etc.")
        if self.start_day is not None and self.unit != "weeks":
            # Keep behavior consistent: weekday scheduling is weekly.
            self.unit = "weeks"

    def _get_interval(self) -> int:
        if self.latest is None:
            return self.interval
        # random.randint is deterministic under patched random/seed; ok.
        return _random.randint(self.interval, self.latest)

    def _schedule_next_run(self, now: Optional[_datetime.datetime] = None) -> None:
        if now is None:
            now = _now()
        self._validate()

        interval = self._get_interval()

        if self.unit == "seconds":
            next_run = now + _datetime.timedelta(seconds=interval)
        elif self.unit == "minutes":
            next_run = now + _datetime.timedelta(minutes=interval)
            if self.at_time is not None:
                # align seconds to at_time.second (and minute to at_time.minute when interval is 1)
                next_run = next_run.replace(second=self.at_time.second, microsecond=0)
        elif self.unit == "hours":
            next_run = now + _datetime.timedelta(hours=interval)
            if self.at_time is not None:
                next_run = next_run.replace(
                    minute=self.at_time.minute, second=self.at_time.second, microsecond=0
                )
        elif self.unit == "days":
            if self.at_time is None:
                next_run = now + _datetime.timedelta(days=interval)
            else:
                # schedule at a specific time of day
                candidate = now.replace(
                    hour=self.at_time.hour,
                    minute=self.at_time.minute,
                    second=self.at_time.second,
                    microsecond=0,
                )
                if candidate <= now:
                    candidate += _datetime.timedelta(days=interval)
                next_run = candidate
        elif self.unit == "weeks":
            # Weekly interval; optionally on a specific weekday and/or at time
            if self.at_time is None:
                at_time = _datetime.time(0, 0, 0)
            else:
                at_time = self.at_time

            # Base candidate is today at at_time
            candidate = now.replace(
                hour=at_time.hour, minute=at_time.minute, second=at_time.second, microsecond=0
            )

            if self.start_day is None:
                # Every N weeks from now; if time already passed today, jump by interval weeks.
                if candidate <= now:
                    candidate += _datetime.timedelta(weeks=interval)
                else:
                    # candidate is later today; but for interval>1, still within this week
                    # Reference behavior effectively schedules the next occurrence; keep it.
                    pass
                next_run = candidate
            else:
                # Next occurrence of weekday start_day at at_time, then add (interval-1) weeks if needed.
                days_ahead = (self.start_day - now.weekday()) % 7
                candidate = candidate + _datetime.timedelta(days=days_ahead)
                if candidate <= now:
                    candidate += _datetime.timedelta(weeks=1)
                # If interval > 1, ensure we respect it by advancing in whole weeks.
                if interval > 1:
                    # Align to the next run that is at least interval weeks away from the most recent
                    # matching weekday. If we already picked next week's candidate (or this week's),
                    # advance by (interval-1) weeks.
                    candidate += _datetime.timedelta(weeks=interval - 1)
                next_run = candidate
        else:
            raise ValueError(f"Invalid unit: {self.unit}")

        # Ensure microsecond=0 for determinism like reference
        if next_run is not None:
            next_run = next_run.replace(microsecond=0)
        self.next_run = next_run


# --- module-level default scheduler and conveniences ---
default_scheduler = Scheduler()


def every(interval: int = 1) -> Job:
    return default_scheduler.every(interval)


# Convenience passthroughs commonly present in schedule module
def run_pending() -> None:
    default_scheduler.run_pending()


def run_all(delay_seconds: int = 0) -> None:
    default_scheduler.run_all(delay_seconds=delay_seconds)


def clear(tag: Optional[Union[str, Sequence[str]]] = None) -> None:
    default_scheduler.clear(tag=tag)


def cancel_job(job: Job) -> None:
    default_scheduler.cancel_job(job)


def next_run() -> Optional[_datetime.datetime]:
    return default_scheduler.next_run


def idle_seconds() -> Optional[float]:
    return default_scheduler.idle_seconds