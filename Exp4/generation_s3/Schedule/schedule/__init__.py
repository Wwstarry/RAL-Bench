"""
A small, pure-Python job scheduling library, compatible with the core API of
the reference "schedule" project.

This module is intentionally self-contained in a single file.
"""

from __future__ import annotations

import datetime as datetime
import functools
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Hashable, List, Optional, Set, Union


def _now() -> datetime.datetime:
    """Indirection point for current time to support deterministic tests."""
    return datetime.datetime.now()


class ScheduleValueError(ValueError):
    """Raised for invalid schedule configuration."""


_WEEKDAY_NAME_TO_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _is_hashable(x: Any) -> bool:
    try:
        hash(x)
        return True
    except Exception:
        return False


def _days_to_weekday(from_weekday: int, to_weekday: int) -> int:
    """Days forward to reach weekday 'to_weekday' from 'from_weekday' (0..6)."""
    return (to_weekday - from_weekday) % 7


def _parse_time_string(time_str: str) -> datetime.time:
    """
    Parse "HH:MM" or "HH:MM:SS" (24h). Returns datetime.time.
    """
    if not isinstance(time_str, str):
        raise ScheduleValueError("time_str must be a string")

    parts = time_str.strip().split(":")
    if len(parts) not in (2, 3):
        raise ScheduleValueError("Invalid time format, expected HH:MM or HH:MM:SS")

    try:
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) == 3 else 0
    except Exception as e:
        raise ScheduleValueError("Invalid time format") from e

    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        raise ScheduleValueError("Invalid time components")

    return datetime.time(hour=hour, minute=minute, second=second)


def _parse_hourly_at(time_str: str) -> datetime.time:
    """
    Parse forms accepted for hourly jobs:
      - ":MM" -> minute within hour
      - "MM:SS" -> minute and second within hour
      - "MM" -> minute within hour
    Returns time with hour=0 (placeholder) and minute/second set.
    """
    if not isinstance(time_str, str):
        raise ScheduleValueError("time_str must be a string")

    s = time_str.strip()
    if not s:
        raise ScheduleValueError("Invalid time format")

    if s.startswith(":"):
        # ":MM" or ":MM:SS"
        s2 = s[1:]
        parts = s2.split(":") if s2 else []
        if len(parts) == 1:
            mm = parts[0]
            ss = "0"
        elif len(parts) == 2:
            mm, ss = parts
        else:
            raise ScheduleValueError("Invalid time format for hourly .at()")
        try:
            minute = int(mm)
            second = int(ss)
        except Exception as e:
            raise ScheduleValueError("Invalid time format for hourly .at()") from e
        if not (0 <= minute <= 59 and 0 <= second <= 59):
            raise ScheduleValueError("Invalid time components for hourly .at()")
        return datetime.time(hour=0, minute=minute, second=second)

    parts = s.split(":")
    if len(parts) == 1:
        # "MM"
        try:
            minute = int(parts[0])
        except Exception as e:
            raise ScheduleValueError("Invalid time format for hourly .at()") from e
        if not (0 <= minute <= 59):
            raise ScheduleValueError("Invalid minute for hourly .at()")
        return datetime.time(hour=0, minute=minute, second=0)

    if len(parts) == 2:
        # "MM:SS"
        try:
            minute = int(parts[0])
            second = int(parts[1])
        except Exception as e:
            raise ScheduleValueError("Invalid time format for hourly .at()") from e
        if not (0 <= minute <= 59 and 0 <= second <= 59):
            raise ScheduleValueError("Invalid time components for hourly .at()")
        return datetime.time(hour=0, minute=minute, second=second)

    raise ScheduleValueError("Invalid time format for hourly .at()")


@dataclass
class CancelJob:
    """Compatibility shim: users can return schedule.CancelJob to cancel."""
    pass


class Job:
    """
    A periodic job.

    Fluent API mirrors reference schedule:
      schedule.every(10).seconds.do(func)
      schedule.every().day.at("10:30").do(func)
      schedule.every().monday.at("08:00").do(func)
    """

    def __init__(self, interval: int, scheduler: "Scheduler"):
        if not isinstance(interval, int):
            raise ValueError("interval must be an int")
        if interval <= 0:
            raise ValueError("interval must be > 0")
        self.interval: int = interval
        self.latest: Optional[int] = None

        self.scheduler: Scheduler = scheduler
        self.unit: Optional[str] = None  # "seconds", "minutes", "hours", "days", "weeks"
        self.at_time: Optional[datetime.time] = None

        # Weekday start marker (0=Mon..6=Sun) for weekly schedules.
        self.start_day: Optional[int] = None

        self.job_func: Optional[Callable] = None
        self.job_func_args: tuple = ()
        self.job_func_kwargs: dict = {}

        self.last_run: Optional[datetime.datetime] = None
        self.next_run: Optional[datetime.datetime] = None

        self.tags: Set[Hashable] = set()

    def __repr__(self) -> str:
        return (
            f"<Job interval={self.interval!r}"
            f"{'..'+str(self.latest) if self.latest is not None else ''}"
            f" unit={self.unit!r} at_time={self.at_time!r} start_day={self.start_day!r}"
            f" next_run={self.next_run!r} last_run={self.last_run!r}>"
        )

    # --- fluent unit properties ---
    @property
    def seconds(self) -> "Job":
        self.unit = "seconds"
        self.start_day = None
        return self

    @property
    def second(self) -> "Job":
        return self.seconds

    @property
    def minutes(self) -> "Job":
        self.unit = "minutes"
        self.start_day = None
        return self

    @property
    def minute(self) -> "Job":
        return self.minutes

    @property
    def hours(self) -> "Job":
        self.unit = "hours"
        self.start_day = None
        return self

    @property
    def hour(self) -> "Job":
        return self.hours

    @property
    def days(self) -> "Job":
        self.unit = "days"
        self.start_day = None
        return self

    @property
    def day(self) -> "Job":
        return self.days

    @property
    def weeks(self) -> "Job":
        self.unit = "weeks"
        # keep start_day as-is if user set weekday
        return self

    @property
    def week(self) -> "Job":
        return self.weeks

    # --- weekday properties (weekly schedule on specific day) ---
    def _set_weekday(self, day_name: str) -> "Job":
        self.unit = "weeks"
        self.start_day = _WEEKDAY_NAME_TO_INDEX[day_name]
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

    def at(self, time_str: str) -> "Job":
        """
        Specify a particular time:
          - For daily/weekly: "HH:MM" or "HH:MM:SS"
          - For hourly: ":MM", "MM", or "MM:SS" (minute/second within the hour)
        """
        if self.unit is None:
            raise ScheduleValueError("Cannot set .at() before selecting a time unit")

        if self.unit in ("days", "weeks"):
            self.at_time = _parse_time_string(time_str)
            return self

        if self.unit == "hours":
            self.at_time = _parse_hourly_at(time_str)
            return self

        raise ScheduleValueError(".at() is only valid for hourly, daily, or weekly jobs")

    def to(self, latest: int) -> "Job":
        """Randomized interval range [interval, latest] inclusive."""
        if not isinstance(latest, int):
            raise ValueError("latest must be an int")
        if latest < self.interval:
            raise ScheduleValueError("latest must be >= interval")
        self.latest = latest
        return self

    def tag(self, *tags: Hashable) -> "Job":
        for t in tags:
            if not _is_hashable(t):
                raise TypeError("Tags must be hashable")
            self.tags.add(t)
        return self

    def do(self, job_func: Callable, *args: Any, **kwargs: Any) -> "Job":
        if not callable(job_func):
            raise ValueError("job_func must be callable")
        self.job_func = functools.partial(job_func, *args, **kwargs)
        self.job_func_args = args
        self.job_func_kwargs = kwargs
        self._schedule_next_run()
        return self

    @property
    def should_run(self) -> bool:
        return self.next_run is not None and _now() >= self.next_run

    def run(self) -> Any:
        if self.job_func is None:
            raise ValueError("Cannot run job: no job function configured (call .do())")

        ret = self.job_func()
        self.last_run = _now()

        # Returning CancelJob is supported by the reference library.
        if ret is CancelJob or isinstance(ret, CancelJob):
            self.scheduler.cancel_job(self)
            return ret

        self._schedule_next_run()
        return ret

    # --- scheduling internals ---
    def _get_interval(self) -> int:
        if self.latest is None:
            return self.interval
        # Tests may monkeypatch random.randint for determinism.
        return int(random.randint(self.interval, self.latest))

    def _schedule_next_run(self) -> None:
        if self.unit is None:
            raise ScheduleValueError("Cannot schedule a job without a unit (e.g. .seconds, .day)")

        now = _now()

        # Base reference moment: last_run if exists else now
        ref = self.last_run or now
        interval = self._get_interval()

        if self.unit == "seconds":
            self.next_run = ref + datetime.timedelta(seconds=interval)
            return

        if self.unit == "minutes":
            self.next_run = ref + datetime.timedelta(minutes=interval)
            return

        if self.unit == "hours":
            self.next_run = ref + datetime.timedelta(hours=interval)
            # Adjust to at_time within the hour if provided.
            if self.at_time is not None:
                candidate = self.next_run.replace(
                    minute=self.at_time.minute,
                    second=self.at_time.second,
                    microsecond=0,
                )
                # If that lands in the past relative to ref/now, push forward an hour.
                if candidate < now:
                    candidate = candidate + datetime.timedelta(hours=1)
                self.next_run = candidate
            return

        if self.unit == "days":
            if self.at_time is None:
                self.next_run = ref + datetime.timedelta(days=interval)
                return

            # Determine next occurrence of at_time; align from "now", not from ref+interval.
            base = now.replace(
                hour=self.at_time.hour,
                minute=self.at_time.minute,
                second=self.at_time.second,
                microsecond=0,
            )
            if base < now:
                base = base + datetime.timedelta(days=1)

            # Apply interval spacing: every N days from the aligned occurrence.
            if interval > 1:
                base = base + datetime.timedelta(days=interval - 1)

            self.next_run = base
            return

        if self.unit == "weeks":
            # Determine the target time-of-day.
            if self.at_time is not None:
                target_time = self.at_time
            else:
                # Keep current time-of-day if not specified.
                target_time = datetime.time(
                    hour=now.hour, minute=now.minute, second=now.second
                )

            # Find the next occurrence of start_day (if set).
            if self.start_day is not None:
                days_ahead = _days_to_weekday(now.weekday(), self.start_day)
                candidate_date = (now + datetime.timedelta(days=days_ahead)).date()
                candidate = datetime.datetime.combine(candidate_date, target_time).replace(
                    microsecond=0
                )
                if candidate < now:
                    candidate = candidate + datetime.timedelta(days=7)
                # Apply interval weeks spacing
                if interval > 1:
                    candidate = candidate + datetime.timedelta(weeks=interval - 1)
                self.next_run = candidate
                return

            # No specific weekday: every N weeks from now at target_time
            candidate = now.replace(
                hour=target_time.hour,
                minute=target_time.minute,
                second=target_time.second,
                microsecond=0,
            )
            if candidate < now:
                candidate = candidate + datetime.timedelta(days=7)
            if interval > 1:
                candidate = candidate + datetime.timedelta(weeks=interval - 1)
            self.next_run = candidate
            return

        raise ScheduleValueError(f"Invalid unit {self.unit!r}")


class Scheduler:
    def __init__(self) -> None:
        self.jobs: List[Job] = []

    def __repr__(self) -> str:
        return f"<Scheduler jobs={len(self.jobs)} next_run={self.next_run!r}>"

    def every(self, interval: int = 1) -> Job:
        job = Job(interval=interval, scheduler=self)
        self.jobs.append(job)
        return job

    def run_pending(self) -> None:
        # Sort by next_run; None last
        runnable: List[Job] = []
        for job in sorted(self.jobs, key=lambda j: (j.next_run is None, j.next_run)):
            if job.should_run:
                runnable.append(job)

        # Run each due job once.
        for job in runnable:
            job.run()

    def run_all(self, delay_seconds: int = 0) -> None:
        if delay_seconds is None:
            delay_seconds = 0
        if delay_seconds < 0:
            raise ValueError("delay_seconds must be >= 0")

        # Run jobs in the order they were scheduled (matches expectation).
        for i, job in enumerate(list(self.jobs)):
            job.run()
            if delay_seconds and i != len(self.jobs) - 1:
                time.sleep(delay_seconds)

    def cancel_job(self, job: Job) -> None:
        try:
            self.jobs.remove(job)
        except ValueError:
            pass

    def clear(self, tag: Any = None) -> None:
        if tag is None:
            self.jobs[:] = []
            return
        self.jobs[:] = [job for job in self.jobs if tag not in job.tags]

    def get_jobs(self, tag: Any = None) -> List[Job]:
        if tag is None:
            return list(self.jobs)
        return [job for job in self.jobs if tag in job.tags]

    @property
    def next_run(self) -> Optional[datetime.datetime]:
        next_runs = [job.next_run for job in self.jobs if job.next_run is not None]
        return min(next_runs) if next_runs else None

    @property
    def idle_seconds(self) -> Optional[float]:
        nr = self.next_run
        if nr is None:
            return None
        return (nr - _now()).total_seconds()


# --- module-level default scheduler and convenience API ---

default_scheduler = Scheduler()


def every(interval: int = 1) -> Job:
    return default_scheduler.every(interval)


def run_pending() -> None:
    return default_scheduler.run_pending()


def run_all(delay_seconds: int = 0) -> None:
    return default_scheduler.run_all(delay_seconds=delay_seconds)


def clear(tag: Any = None) -> None:
    return default_scheduler.clear(tag=tag)


def cancel_job(job: Job) -> None:
    return default_scheduler.cancel_job(job)


def get_jobs(tag: Any = None) -> List[Job]:
    return default_scheduler.get_jobs(tag=tag)