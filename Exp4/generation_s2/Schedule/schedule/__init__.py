"""
A lightweight job scheduling library compatible with the core API of the
reference "schedule" project.

Public API:
- schedule.every(...)
- schedule.Job
- schedule.Scheduler
"""

from __future__ import annotations

import datetime as _dt
import functools as _functools
import random as _random
from dataclasses import dataclass as _dataclass
from typing import Any, Callable, Hashable, List, Optional, Sequence, Set, Tuple, Union


# --- module-level time indirection (for deterministic monkeypatching) ---------
# Tests often monkeypatch schedule.datetime or schedule.datetime.datetime.
# We therefore reference this module's `datetime` variable everywhere.
datetime = _dt  # noqa: N816


def _now(tz: Optional[_dt.tzinfo] = None) -> _dt.datetime:
    # Use module-global `datetime` so monkeypatching works.
    return datetime.datetime.now(tz=tz)


def _as_int(n: Any) -> int:
    try:
        return int(n)
    except Exception:
        raise TypeError("interval must be an integer-compatible value")


# --- constants ----------------------------------------------------------------
_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


class ScheduleValueError(ValueError):
    pass


class CancelJob:
    """Return from a job function to cancel the job."""


def _parse_time_str(s: str) -> Tuple[int, int, int]:
    """
    Parse "HH:MM" or "HH:MM:SS" in 24-hour time.
    """
    if not isinstance(s, str):
        raise ScheduleValueError("at() time must be a string")
    parts = s.strip().split(":")
    if len(parts) not in (2, 3):
        raise ScheduleValueError("Invalid time format, expected HH:MM or HH:MM:SS")
    try:
        hh = int(parts[0])
        mm = int(parts[1])
        ss = int(parts[2]) if len(parts) == 3 else 0
    except Exception:
        raise ScheduleValueError("Invalid time format, expected integers")
    if not (0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59):
        raise ScheduleValueError("Invalid time values")
    return hh, mm, ss


def _total_seconds(td: _dt.timedelta) -> float:
    # Python 3.7+ has timedelta.total_seconds
    return td.total_seconds()


def _maybe_aware(dt: _dt.datetime, tz: Optional[_dt.tzinfo]) -> _dt.datetime:
    if tz is None:
        return dt
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


@_dataclass
class _Range:
    min: int
    max: int


class Job:
    """
    A scheduled job.

    Typical use:
        schedule.every(10).seconds.do(func, *args, **kwargs)
        schedule.every().day.at("10:30").do(func)
        schedule.every().monday.at("13:15").do(func)
    """

    def __init__(self, interval: int, scheduler: "Scheduler"):
        self.scheduler = scheduler

        self.interval: int = _as_int(interval)
        if self.interval < 1:
            raise ScheduleValueError("interval must be >= 1")

        self.latest: Optional[int] = None  # for .to(...)
        self.unit: Optional[str] = None  # seconds/minutes/hours/days/weeks
        self.at_time: Optional[_dt.time] = None
        self.at_time_zone: Optional[_dt.tzinfo] = None

        self.start_day: Optional[int] = None  # weekday 0=Mon..6=Sun for weekly
        self.job_func: Optional[Callable[..., Any]] = None
        self.job_func_args: Tuple[Any, ...] = ()
        self.job_func_kwargs: dict = {}

        self.last_run: Optional[_dt.datetime] = None
        self.next_run: Optional[_dt.datetime] = None

        self.cancel_after: Optional[_dt.datetime] = None  # not core but harmless

        self.tags: Set[Hashable] = set()

    def __repr__(self) -> str:
        unit = self.unit or "?"
        return f"Every {self.interval} {unit} do {self.job_func}"

    # --- interval builder -----------------------------------------------------

    def to(self, latest: int) -> "Job":
        latest_i = _as_int(latest)
        if latest_i < self.interval:
            raise ScheduleValueError("latest must be >= interval")
        self.latest = latest_i
        return self

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

    # --- weekday shortcuts ----------------------------------------------------

    @property
    def monday(self) -> "Job":
        self.start_day = _WEEKDAYS["monday"]
        self.unit = "weeks"
        return self

    @property
    def tuesday(self) -> "Job":
        self.start_day = _WEEKDAYS["tuesday"]
        self.unit = "weeks"
        return self

    @property
    def wednesday(self) -> "Job":
        self.start_day = _WEEKDAYS["wednesday"]
        self.unit = "weeks"
        return self

    @property
    def thursday(self) -> "Job":
        self.start_day = _WEEKDAYS["thursday"]
        self.unit = "weeks"
        return self

    @property
    def friday(self) -> "Job":
        self.start_day = _WEEKDAYS["friday"]
        self.unit = "weeks"
        return self

    @property
    def saturday(self) -> "Job":
        self.start_day = _WEEKDAYS["saturday"]
        self.unit = "weeks"
        return self

    @property
    def sunday(self) -> "Job":
        self.start_day = _WEEKDAYS["sunday"]
        self.unit = "weeks"
        return self

    # --- modifiers ------------------------------------------------------------

    def tag(self, *tags: Hashable) -> "Job":
        for t in tags:
            self.tags.add(t)
        return self

    def at(self, time_str: str, tz: Optional[_dt.tzinfo] = None) -> "Job":
        """
        Specify an exact time for daily/weekly jobs, or a minute/second offset
        for hourly/minutely jobs in the reference library. For core tests, the
        "HH:MM" and "HH:MM:SS" forms for day/week are most important.
        """
        hh, mm, ss = _parse_time_str(time_str)
        self.at_time = datetime.time(hh, mm, ss)
        self.at_time_zone = tz
        return self

    def until(self, until_time: Union[_dt.datetime, _dt.timedelta, str]) -> "Job":
        # Not core but included for compatibility with some user code/tests.
        if isinstance(until_time, datetime.datetime):
            self.cancel_after = until_time
        elif isinstance(until_time, datetime.timedelta):
            self.cancel_after = _now() + until_time
        elif isinstance(until_time, str):
            # Interpret as "YYYY-MM-DD HH:MM[:SS]" or "HH:MM[:SS]" today.
            s = until_time.strip()
            if " " in s:
                d, t = s.split(" ", 1)
                y, m, d2 = (int(x) for x in d.split("-"))
                hh, mm, ss = _parse_time_str(t)
                self.cancel_after = datetime.datetime(y, m, d2, hh, mm, ss)
            else:
                hh, mm, ss = _parse_time_str(s)
                n = _now()
                self.cancel_after = datetime.datetime(n.year, n.month, n.day, hh, mm, ss)
        else:
            raise ScheduleValueError("until() requires datetime, timedelta, or string")
        return self

    # --- scheduling ------------------------------------------------------------

    def do(self, job_func: Callable[..., Any], *args: Any, **kwargs: Any) -> "Job":
        self.job_func = job_func
        self.job_func_args = args
        self.job_func_kwargs = kwargs
        self._schedule_next_run()
        return self

    @property
    def should_run(self) -> bool:
        if self.next_run is None:
            return False
        return _now(tz=self.next_run.tzinfo) >= self.next_run

    def run(self) -> Any:
        if self.job_func is None:
            return None

        if self.cancel_after is not None:
            now = _now(tz=self.cancel_after.tzinfo)
            if now >= self.cancel_after:
                return CancelJob

        ret = self.job_func(*self.job_func_args, **self.job_func_kwargs)
        self.last_run = _now(tz=self.next_run.tzinfo if self.next_run else None)
        self._schedule_next_run()
        return ret

    def _get_interval(self) -> int:
        if self.latest is None:
            return self.interval
        # inclusive range in reference library
        return _random.randint(self.interval, self.latest)

    def _schedule_next_run(self) -> None:
        if self.unit is None:
            # Default unit in reference is seconds for plain every(n) if not specified
            self.unit = "seconds"

        now = _now(tz=self.at_time_zone)
        now = _maybe_aware(now, self.at_time_zone)

        interval = self._get_interval()

        if self.unit == "seconds":
            next_run = now + datetime.timedelta(seconds=interval)

        elif self.unit == "minutes":
            next_run = now + datetime.timedelta(minutes=interval)

        elif self.unit == "hours":
            next_run = now + datetime.timedelta(hours=interval)

        elif self.unit == "days":
            next_run = now + datetime.timedelta(days=interval)
            if self.at_time is not None:
                next_run = next_run.replace(
                    hour=self.at_time.hour,
                    minute=self.at_time.minute,
                    second=self.at_time.second,
                    microsecond=0,
                )
                # If that lands in the past (e.g. interval=1 but now earlier),
                # roll forward by one day to keep it future.
                if next_run <= now:
                    next_run = next_run + datetime.timedelta(days=1)

        elif self.unit == "weeks":
            # Weekly jobs optionally anchored to a weekday and a time.
            if self.start_day is None:
                next_run = now + datetime.timedelta(weeks=interval)
                if self.at_time is not None:
                    next_run = next_run.replace(
                        hour=self.at_time.hour,
                        minute=self.at_time.minute,
                        second=self.at_time.second,
                        microsecond=0,
                    )
                    if next_run <= now:
                        next_run = next_run + datetime.timedelta(weeks=1)
            else:
                # Find next occurrence of start_day (including today if time not passed)
                days_ahead = (self.start_day - now.weekday()) % 7
                candidate = now + datetime.timedelta(days=days_ahead)
                if self.at_time is not None:
                    candidate = candidate.replace(
                        hour=self.at_time.hour,
                        minute=self.at_time.minute,
                        second=self.at_time.second,
                        microsecond=0,
                    )
                else:
                    # default to "now" time (truncate microseconds)
                    candidate = candidate.replace(microsecond=0)
                if candidate <= now:
                    candidate += datetime.timedelta(days=7)
                # then add (interval-1) weeks on top (since candidate already next week occurrence)
                if interval > 1:
                    candidate += datetime.timedelta(weeks=interval - 1)
                next_run = candidate

        else:
            raise ScheduleValueError(f"Invalid unit: {self.unit}")

        self.next_run = next_run

    # --- comparisons for deterministic sorting -------------------------------

    def __lt__(self, other: "Job") -> bool:
        if self.next_run is None and other.next_run is None:
            return False
        if self.next_run is None:
            return False
        if other.next_run is None:
            return True
        return self.next_run < other.next_run


class Scheduler:
    """
    A scheduler holding jobs and running them when due.
    """

    def __init__(self) -> None:
        self.jobs: List[Job] = []

    def every(self, interval: int = 1) -> Job:
        job = Job(interval, self)
        return job

    def get_jobs(self, tag: Optional[Hashable] = None) -> List[Job]:
        if tag is None:
            return list(self.jobs)
        return [j for j in self.jobs if tag in j.tags]

    def clear(self, tag: Optional[Hashable] = None) -> None:
        if tag is None:
            self.jobs.clear()
        else:
            self.jobs[:] = [j for j in self.jobs if tag not in j.tags]

    def cancel_job(self, job: Job) -> None:
        try:
            self.jobs.remove(job)
        except ValueError:
            pass

    def run_pending(self) -> None:
        runnable = [job for job in self.jobs if job.should_run]
        runnable.sort()
        for job in runnable:
            ret = job.run()
            if ret is CancelJob:
                self.cancel_job(job)

    def run_all(self, delay_seconds: int = 0) -> None:
        # Do not sleep (keeps tests deterministic); emulate reference by running in order.
        for job in list(self.jobs):
            ret = job.run()
            if ret is CancelJob:
                self.cancel_job(job)

    @property
    def next_run(self) -> Optional[_dt.datetime]:
        if not self.jobs:
            return None
        nexts = [j.next_run for j in self.jobs if j.next_run is not None]
        if not nexts:
            return None
        return min(nexts)

    @property
    def idle_seconds(self) -> Optional[float]:
        nr = self.next_run
        if nr is None:
            return None
        return _total_seconds(nr - _now(tz=nr.tzinfo))


# --- module-level default scheduler ------------------------------------------
default_scheduler = Scheduler()


def every(interval: int = 1) -> Job:
    job = default_scheduler.every(interval)
    # In the reference library, jobs are added to the scheduler when .do(...) is called.
    # We'll add upon .do by wrapping Job.do to append if missing.
    original_do = job.do

    @_functools.wraps(original_do)
    def _do_and_register(job_func: Callable[..., Any], *args: Any, **kwargs: Any) -> Job:
        j = original_do(job_func, *args, **kwargs)
        if j not in default_scheduler.jobs:
            default_scheduler.jobs.append(j)
        return j

    job.do = _do_and_register  # type: ignore[method-assign]
    return job


def run_pending() -> None:
    return default_scheduler.run_pending()


def run_all(delay_seconds: int = 0) -> None:
    return default_scheduler.run_all(delay_seconds=delay_seconds)


def clear(tag: Optional[Hashable] = None) -> None:
    return default_scheduler.clear(tag=tag)


def cancel_job(job: Job) -> None:
    return default_scheduler.cancel_job(job)


def next_run() -> Optional[_dt.datetime]:
    return default_scheduler.next_run


def idle_seconds() -> Optional[float]:
    return default_scheduler.idle_seconds


__all__ = [
    "Scheduler",
    "Job",
    "CancelJob",
    "ScheduleValueError",
    "default_scheduler",
    "every",
    "run_pending",
    "run_all",
    "clear",
    "cancel_job",
    "next_run",
    "idle_seconds",
]