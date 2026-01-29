"""
A small, pure-Python job scheduling library compatible with core parts of the
reference 'schedule' project.

This module intentionally keeps implementation in a single file to simplify
import/monkeypatching in tests. All "now" access goes through _now() and uses
the module-level 'datetime' import (not 'from datetime import ...') so that
monkeypatching schedule.datetime or schedule._now works as expected.
"""

from __future__ import annotations

import datetime
import random
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Hashable, Iterable, List, Optional, Set, Tuple


def _now() -> datetime.datetime:
    """Indirection for current time to make monkeypatching deterministic."""
    return datetime.datetime.now()


class ScheduleValueError(ValueError):
    """Raised for invalid scheduling parameters (e.g., .at() usage/format)."""


class _CancelJob:
    def __repr__(self) -> str:  # pragma: no cover
        return "CancelJob"


CancelJob = _CancelJob()


def _weekday_index(name: str) -> int:
    mapping = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    return mapping[name]


def _coerce_int(x: Any, field: str) -> int:
    try:
        v = int(x)
    except Exception as e:
        raise ScheduleValueError(f"{field} must be an integer") from e
    return v


def _validate_time(h: int, m: int, s: int) -> None:
    if not (0 <= h <= 23):
        raise ScheduleValueError("Hour must be in 0..23")
    if not (0 <= m <= 59):
        raise ScheduleValueError("Minute must be in 0..59")
    if not (0 <= s <= 59):
        raise ScheduleValueError("Second must be in 0..59")


def _parse_time_str(time_str: str) -> Tuple[int, int, int]:
    """
    Parse a permissive time string into (hour, minute, second), validating ranges.

    Accepted forms:
      - "HH:MM"
      - "HH:MM:SS"
      - "MM:SS"
      - ":MM" or ":SS"
      - "SS" (single number)

    Interpretation of the returned tuple depends on the unit (.day/.hour/.minute).
    """
    if not isinstance(time_str, str):
        raise ScheduleValueError("time_str must be a string")

    s = time_str.strip()
    if not s:
        raise ScheduleValueError("Invalid time format")

    # ":MM" or ":SS"
    if s.startswith(":"):
        rest = s[1:]
        if not rest.isdigit():
            raise ScheduleValueError("Invalid time format")
        v = int(rest)
        # Return as (0, v, 0) and unit-specific interpretation will use it.
        # This supports both hour.at(":MM") and minute.at(":SS") patterns.
        return (0, v, 0)

    # plain "SS"
    if re.fullmatch(r"\d{1,2}", s):
        v = int(s)
        return (0, 0, v)

    parts = s.split(":")
    if len(parts) == 2:
        a, b = parts
        if not (a.isdigit() and b.isdigit()):
            raise ScheduleValueError("Invalid time format")
        return (int(a), int(b), 0)
    if len(parts) == 3:
        a, b, c = parts
        if not (a.isdigit() and b.isdigit() and c.isdigit()):
            raise ScheduleValueError("Invalid time format")
        return (int(a), int(b), int(c))

    raise ScheduleValueError("Invalid time format")


@dataclass
class _AtTime:
    hour: int
    minute: int
    second: int

    def as_time(self) -> datetime.time:
        return datetime.time(self.hour, self.minute, self.second)


class Scheduler:
    def __init__(self) -> None:
        self.jobs: List[Job] = []

    def every(self, interval: int = 1) -> "Job":
        interval_i = _coerce_int(interval, "interval")
        if interval_i < 1:
            raise ScheduleValueError("interval must be >= 1")
        return Job(interval=interval_i, scheduler=self)

    def run_pending(self) -> List[Any]:
        now = _now()
        runnable = [job for job in self.jobs if job.next_run is not None and job.next_run <= now]
        runnable.sort(key=lambda j: j.next_run or datetime.datetime.max)
        results: List[Any] = []
        for job in list(runnable):
            # job may have been canceled while running an earlier job
            if job not in self.jobs:
                continue
            if not job.should_run:
                continue
            results.append(job.run())
        return results

    def run_all(self, delay_seconds: int = 0) -> List[Any]:
        delay = _coerce_int(delay_seconds, "delay_seconds")
        if delay < 0:
            raise ScheduleValueError("delay_seconds must be >= 0")
        results: List[Any] = []
        for idx, job in enumerate(list(self.jobs)):
            if job not in self.jobs:
                continue
            results.append(job.run())
            if delay and idx != len(self.jobs) - 1:
                time.sleep(delay)
        return results

    def clear(self, tag: Hashable | None = None) -> None:
        if tag is None:
            self.jobs.clear()
            return
        self.jobs[:] = [j for j in self.jobs if tag not in j.tags]

    def cancel_job(self, job: "Job") -> None:
        try:
            self.jobs.remove(job)
        except ValueError:
            return

    def get_jobs(self, tag: Hashable | None = None) -> List["Job"]:
        if tag is None:
            return list(self.jobs)
        return [j for j in self.jobs if tag in j.tags]

    @property
    def next_run(self) -> Optional[datetime.datetime]:
        next_times = [j.next_run for j in self.jobs if j.next_run is not None]
        return min(next_times) if next_times else None

    @property
    def idle_seconds(self) -> Optional[float]:
        nr = self.next_run
        if nr is None:
            return None
        return (nr - _now()).total_seconds()


class Job:
    def __init__(self, interval: int, scheduler: Scheduler) -> None:
        self.scheduler = scheduler
        self.interval: int = interval
        self.latest: Optional[int] = None

        self.unit: Optional[str] = None  # seconds/minutes/hours/days/weeks
        self.start_day: Optional[str] = None  # monday..sunday for weekly jobs
        self.at_time: Optional[_AtTime] = None

        self.job_func: Optional[Callable[..., Any]] = None
        self.job_func_args: Tuple[Any, ...] = ()
        self.job_func_kwargs: dict[str, Any] = {}

        self.tags: Set[Hashable] = set()

        self.last_run: Optional[datetime.datetime] = None
        self.next_run: Optional[datetime.datetime] = None

    # --- Unit properties ---
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

    # --- Weekday properties ---
    def _set_weekday(self, name: str) -> "Job":
        self.start_day = name
        self.unit = "weeks"
        return self

    @property
    def monday(self) -> "Job":
        return self._set_weekday("monday")

    @property
    def tuesday(self) -> "Job":
        return self._set_weekday("tuesday")

    @property
    def wednesday(self) -> "Job":
        return self._set_weekday("wednesday")

    @property
    def thursday(self) -> "Job":
        return self._set_weekday("thursday")

    @property
    def friday(self) -> "Job":
        return self._set_weekday("friday")

    @property
    def saturday(self) -> "Job":
        return self._set_weekday("saturday")

    @property
    def sunday(self) -> "Job":
        return self._set_weekday("sunday")

    # --- Fluent methods ---
    def at(self, time_str: str) -> "Job":
        if self.unit is None:
            raise ScheduleValueError("Cannot set .at() before setting a unit")
        if self.unit == "seconds":
            raise ScheduleValueError(".at() is not supported for second-based jobs")
        if self.unit == "weeks" and self.start_day is None:
            raise ScheduleValueError(".at() is only supported for weekly jobs when a weekday is specified")

        h, m, s = _parse_time_str(time_str)

        if self.unit in ("days", "weeks"):
            # Interpret as absolute HH:MM(:SS). If given "MM:SS" treat as HH=MM, MM=SS (best-effort).
            # If given ":MM" treat as HH=0, MM=value.
            # If given "SS" treat as HH=0, MM=0, SS=value.
            _validate_time(h, m, s)
            self.at_time = _AtTime(h, m, s)
            return self

        if self.unit == "hours":
            # Interpret as minute(:second) within the hour.
            # Accept "HH:MM(:SS)" but ignore HH; accept ":MM" (returned as h=0, m=value, s=0).
            minute = m
            second = s
            if len(time_str.strip().split(":")) == 1 and time_str.strip().isdigit():
                # "SS"
                minute = 0
                second = int(time_str.strip())
            elif time_str.strip().startswith(":"):
                # ":MM"
                minute = int(time_str.strip()[1:])
                second = 0
            elif len(time_str.strip().split(":")) == 2:
                # "HH:MM" or "MM:SS" ambiguous; for hour.at we take last component as minute.
                minute = int(time_str.strip().split(":")[1])
                second = 0
            elif len(time_str.strip().split(":")) == 3:
                # "HH:MM:SS" -> MM:SS
                parts = time_str.strip().split(":")
                minute = int(parts[1])
                second = int(parts[2])

            if not (0 <= minute <= 59):
                raise ScheduleValueError("Minute must be in 0..59")
            if not (0 <= second <= 59):
                raise ScheduleValueError("Second must be in 0..59")
            self.at_time = _AtTime(0, minute, second)
            return self

        if self.unit == "minutes":
            # Interpret as second within the minute.
            # Accept "SS", ":SS", "MM:SS" (use SS), "HH:MM:SS" (use SS).
            second: int
            st = time_str.strip()
            if st.startswith(":"):
                second = int(st[1:]) if st[1:].isdigit() else -1
            else:
                parts = st.split(":")
                if len(parts) == 1 and parts[0].isdigit():
                    second = int(parts[0])
                elif len(parts) == 2 and parts[1].isdigit():
                    second = int(parts[1])
                elif len(parts) == 3 and parts[2].isdigit():
                    second = int(parts[2])
                else:
                    raise ScheduleValueError("Invalid time format")
            if not (0 <= second <= 59):
                raise ScheduleValueError("Second must be in 0..59")
            self.at_time = _AtTime(0, 0, second)
            return self

        raise ScheduleValueError(f"Unsupported unit for .at(): {self.unit}")

    def to(self, latest: int) -> "Job":
        latest_i = _coerce_int(latest, "latest")
        if latest_i < self.interval:
            raise ScheduleValueError("latest must be >= interval")
        self.latest = latest_i
        return self

    def tag(self, *tags: Hashable) -> "Job":
        for t in tags:
            self.tags.add(t)
        return self

    def do(self, job_func: Callable[..., Any], *args: Any, **kwargs: Any) -> "Job":
        if self.unit is None:
            raise ScheduleValueError("Cannot schedule a job without a time unit (e.g., .seconds, .day)")
        self.job_func = job_func
        self.job_func_args = args
        self.job_func_kwargs = kwargs
        self._schedule_next_run()
        if self not in self.scheduler.jobs:
            self.scheduler.jobs.append(self)
        return self

    # --- Execution & scheduling ---
    @property
    def should_run(self) -> bool:
        return self.next_run is not None and _now() >= self.next_run

    def run(self) -> Any:
        if self.job_func is None:
            raise ScheduleValueError("Cannot run a job that has not been scheduled with .do()")
        now = _now()
        ret = self.job_func(*self.job_func_args, **self.job_func_kwargs)
        self.last_run = now
        if ret is CancelJob:
            self.scheduler.cancel_job(self)
            return ret
        self._schedule_next_run()
        return ret

    def _get_interval(self) -> int:
        if self.latest is None:
            return self.interval
        return random.randint(self.interval, self.latest)

    def _schedule_next_run(self) -> None:
        now = _now()
        interval = self._get_interval()

        if self.unit in ("seconds", "minutes", "hours", "days") and self.start_day is not None:
            # start_day only meaningful for weeks
            self.start_day = None

        if self.unit == "seconds":
            self.next_run = now + datetime.timedelta(seconds=interval)
            return
        if self.unit == "minutes":
            self.next_run = self._next_minute_run(now, interval)
            return
        if self.unit == "hours":
            self.next_run = self._next_hour_run(now, interval)
            return
        if self.unit == "days":
            self.next_run = self._next_day_run(now, interval)
            return
        if self.unit == "weeks":
            self.next_run = self._next_week_run(now, interval)
            return

        raise ScheduleValueError(f"Invalid unit: {self.unit}")

    def _next_minute_run(self, now: datetime.datetime, interval: int) -> datetime.datetime:
        if self.at_time is None:
            return now + datetime.timedelta(minutes=interval)
        # at_time.second within minute
        second = self.at_time.second
        candidate = now.replace(microsecond=0)
        candidate = candidate.replace(second=second)
        if candidate <= now.replace(microsecond=0):
            candidate = candidate + datetime.timedelta(minutes=1)
        if interval > 1:
            candidate = candidate + datetime.timedelta(minutes=interval - 1)
        return candidate

    def _next_hour_run(self, now: datetime.datetime, interval: int) -> datetime.datetime:
        if self.at_time is None:
            return now + datetime.timedelta(hours=interval)
        minute = self.at_time.minute
        second = self.at_time.second
        candidate = now.replace(microsecond=0, minute=minute, second=second)
        if candidate <= now.replace(microsecond=0):
            candidate = candidate + datetime.timedelta(hours=1)
        if interval > 1:
            candidate = candidate + datetime.timedelta(hours=interval - 1)
        return candidate

    def _next_day_run(self, now: datetime.datetime, interval: int) -> datetime.datetime:
        if self.at_time is None:
            return now + datetime.timedelta(days=interval)
        t = self.at_time.as_time()
        candidate_date = now.date()
        candidate = datetime.datetime.combine(candidate_date, t)
        if candidate <= now:
            candidate = candidate + datetime.timedelta(days=1)
        if interval > 1:
            candidate = candidate + datetime.timedelta(days=interval - 1)
        return candidate

    def _next_week_run(self, now: datetime.datetime, interval: int) -> datetime.datetime:
        # If no weekday specified, just treat as every N weeks from now (or at_time from now date).
        if self.start_day is None:
            if self.at_time is None:
                return now + datetime.timedelta(weeks=interval)
            # Next run is today at at_time if still in future else tomorrow, then add (interval-1) weeks.
            t = self.at_time.as_time()
            candidate = datetime.datetime.combine(now.date(), t)
            if candidate <= now:
                candidate = candidate + datetime.timedelta(days=1)
            if interval > 1:
                candidate = candidate + datetime.timedelta(weeks=interval - 1)
            return candidate

        target = _weekday_index(self.start_day)
        days_ahead = (target - now.weekday()) % 7
        candidate_date = now.date() + datetime.timedelta(days=days_ahead)

        if self.at_time is not None:
            t = self.at_time.as_time()
        else:
            # Use current time-of-day if not specified, rounded to second.
            t = now.replace(microsecond=0).time()

        candidate = datetime.datetime.combine(candidate_date, t)
        if candidate <= now:
            candidate = candidate + datetime.timedelta(weeks=1)

        if interval > 1:
            candidate = candidate + datetime.timedelta(weeks=interval - 1)

        return candidate

    def __repr__(self) -> str:  # pragma: no cover
        parts = [f"Job(interval={self.interval}"]
        if self.latest is not None:
            parts.append(f"to={self.latest}")
        if self.unit:
            parts.append(f"unit={self.unit}")
        if self.start_day:
            parts.append(f"start_day={self.start_day}")
        if self.at_time:
            parts.append(f"at={self.at_time.hour:02d}:{self.at_time.minute:02d}:{self.at_time.second:02d}")
        if self.next_run:
            parts.append(f"next_run={self.next_run!r}")
        parts.append(")")
        return "<" + " ".join(parts) + ">"


# Default scheduler instance and module-level wrappers (reference-style).
default_scheduler = Scheduler()


def every(interval: int = 1) -> Job:
    return default_scheduler.every(interval)


def run_pending() -> List[Any]:
    return default_scheduler.run_pending()


def run_all(delay_seconds: int = 0) -> List[Any]:
    return default_scheduler.run_all(delay_seconds=delay_seconds)


def clear(tag: Hashable | None = None) -> None:
    return default_scheduler.clear(tag=tag)


def cancel_job(job: Job) -> None:
    return default_scheduler.cancel_job(job)


def get_jobs(tag: Hashable | None = None) -> List[Job]:
    return default_scheduler.get_jobs(tag=tag)


@property
def jobs() -> List[Job]:  # type: ignore[misc]
    # Kept for API similarity; most tests access schedule.jobs as a list.
    return default_scheduler.jobs


def next_run() -> Optional[datetime.datetime]:
    return default_scheduler.next_run


def idle_seconds() -> Optional[float]:
    return default_scheduler.idle_seconds


def repeat(job: Job) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator: @schedule.repeat(schedule.every().day)
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        job.do(func)
        return func
    return decorator


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
    "get_jobs",
    "jobs",
    "next_run",
    "idle_seconds",
    "repeat",
]