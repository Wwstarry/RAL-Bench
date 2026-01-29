"""
A lightweight, pure-python re-implementation of the core parts of the
`schedule` library (https://github.com/dbader/schedule).

Only the public bits that are required by the black-box tests are included:

* schedule.every
* Job class
* Scheduler class
* Aliases that forward to the global default scheduler:
    - run_pending
    - run_all
    - clear
    - cancel_job
"""

from __future__ import annotations

import datetime as _datetime
import functools as _functools
import time as _time
from types import SimpleNamespace
from typing import Any, Callable, Iterable, List, Optional, Sequence, Set

__all__ = [
    "every",
    "Job",
    "Scheduler",
    # Forwarded helpers
    "run_pending",
    "run_all",
    "clear",
    "cancel_job",
]

# --------------------------------------------------------------------------- #
# Monkey-patch friendly helpers
# --------------------------------------------------------------------------- #

# The tests of the original project monkey-patch the module attributes directly
# (e.g. ``schedule._datetime``) to control the perceived now()/sleep()
# semantics.  We therefore re-export the modules as variables instead of using
# them directly.  ONLY read those variables – never rebind them!
_datetime_module = _datetime
_time_module = _time


def _now() -> _datetime.datetime:
    """Return *now* based on the (patchable) ``_datetime_module``."""
    return _datetime_module.datetime.now()


def _sleep(seconds: float) -> None:
    """A ``time.sleep`` clone that honours monkey-patching."""
    _time_module.sleep(seconds)


# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #


class ScheduleError(RuntimeError):
    """Generic scheduling error (mirrors upstream API)."""


# --------------------------------------------------------------------------- #
# Job
# --------------------------------------------------------------------------- #


class Job:
    """
    A *Job* represents a scheduled callable with metadata describing when the
    callable should be executed next.
    """

    WEEKDAYS: List[str] = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]

    def __init__(self, interval: int, scheduler: "Scheduler"):
        if interval <= 0:
            raise ScheduleError("Interval must be > 0")
        self.scheduler: "Scheduler" = scheduler
        self.interval: int = interval  # e.g. 5
        self.unit: Optional[str] = None  # 'seconds', 'minutes', ...
        self.at_time: Optional[_datetime.time] = None
        self.start_day: Optional[str] = None  # 'monday', ...
        self.job_func: Optional[Callable[..., Any]] = None
        self.args: Sequence[Any] = ()
        self.kwargs: dict[str, Any] = {}
        self.last_run: Optional[_datetime.datetime] = None
        self.next_run: Optional[_datetime.datetime] = None
        self._tags: Set[str] = set()

    # --------------------------------------------------------------------- #
    # Interval helpers (singular + plural)
    # --------------------------------------------------------------------- #

    def _set_unit(self, unit: str) -> "Job":
        self.unit = unit
        return self

    # Seconds
    @property
    def seconds(self) -> "Job":  # noqa: D401
        return self._set_unit("seconds")

    @property
    def second(self) -> "Job":  # noqa: D401
        return self.seconds

    # Minutes
    @property
    def minutes(self) -> "Job":  # noqa: D401
        return self._set_unit("minutes")

    @property
    def minute(self) -> "Job":  # noqa: D401
        return self.minutes

    # Hours
    @property
    def hours(self) -> "Job":  # noqa: D401
        return self._set_unit("hours")

    @property
    def hour(self) -> "Job":  # noqa: D401
        return self.hours

    # Days
    @property
    def days(self) -> "Job":  # noqa: D401
        return self._set_unit("days")

    @property
    def day(self) -> "Job":  # noqa: D401
        return self.days

    # Weeks
    @property
    def weeks(self) -> "Job":  # noqa: D401
        return self._set_unit("weeks")

    @property
    def week(self) -> "Job":  # noqa: D401
        return self.weeks

    # Weekdays – each property sets ``start_day`` and unit == weeks
    def _weekday_property(name: str, index: int):
        def _getter(self: "Job") -> "Job":  # noqa: D401
            self.unit = "weeks"
            self.start_day = name
            return self

        _getter.__name__ = name
        return property(_getter)

    # Dynamically add properties for monday…sunday
    for idx, _name in enumerate(WEEKDAYS):
        locals()[_name] = _weekday_property(_name, idx)
    del idx, _name, _weekday_property  # cleanup namespace

    # --------------------------------------------------------------------- #
    # DSL: .at("HH:MM") / .at(":MM")
    # --------------------------------------------------------------------- #

    def at(self, time_str: str) -> "Job":
        """
        Specify the specific time of day (or minute within the hour) when the
        job should run.

        Accepted formats (mirrors upstream behaviour for common cases):
        * "HH:MM"
        * "HH:MM:SS"
        * ":MM"
        * ":MM:SS"
        """
        self.at_time = self._parse_time(time_str)
        return self

    @staticmethod
    def _parse_time(time_str: str) -> _datetime.time:
        if not isinstance(time_str, str):
            raise ScheduleError("at() expects a string like 'HH:MM'")
        if time_str.startswith(":"):
            # Format ":MM" or ":MM:SS" – implies current hour == 0
            parts = time_str[1:].split(":")
            if len(parts) not in (1, 2):
                raise ScheduleError(f"Invalid time format {time_str!r}")
            minute = int(parts[0])
            second = int(parts[1]) if len(parts) == 2 else 0
            return _datetime_module.time(hour=0, minute=minute, second=second)
        parts = time_str.split(":")
        if len(parts) not in (2, 3):
            raise ScheduleError(f"Invalid time format {time_str!r}")
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) == 3 else 0
        return _datetime_module.time(hour=hour, minute=minute, second=second)

    # --------------------------------------------------------------------- #
    # DSL: tagging
    # --------------------------------------------------------------------- #

    def tag(self, *tags: str) -> "Job":
        """Attach one or more textual tags to the job."""
        for t in tags:
            if not isinstance(t, str):
                raise ScheduleError("Tags must be str")
            self._tags.add(t)
        return self

    @property
    def tags(self) -> Set[str]:
        return set(self._tags)

    # --------------------------------------------------------------------- #
    # Scheduling
    # --------------------------------------------------------------------- #

    def _schedule_next_run(self) -> None:
        """Compute ``self.next_run`` based on current settings."""
        if self.unit is None:
            raise ScheduleError("Time unit (seconds, minutes, …) was not set")
        now = _now()

        # Seconds / Minutes / Hours – ignore .at()
        if self.unit == "seconds":
            self.next_run = now + _datetime_module.timedelta(seconds=self.interval)
            return
        if self.unit == "minutes":
            self.next_run = now + _datetime_module.timedelta(minutes=self.interval)
            return
        if self.unit == "hours":
            # Round down to the start of the current hour for deterministic
            # scheduling (mirrors upstream semantics).
            next_run = now.replace(minute=0, second=0, microsecond=0)
            if self.at_time:
                # at_time's minute/second inside the hour
                next_run = next_run.replace(
                    minute=self.at_time.minute, second=self.at_time.second
                )
                if next_run <= now:
                    next_run += _datetime_module.timedelta(hours=self.interval)
            else:
                next_run += _datetime_module.timedelta(hours=self.interval)
            self.next_run = next_run
            return

        # Days
        if self.unit == "days":
            next_run = now + _datetime_module.timedelta(days=self.interval)
            if self.at_time:
                candidate = now.replace(
                    hour=self.at_time.hour,
                    minute=self.at_time.minute,
                    second=self.at_time.second,
                    microsecond=0,
                )
                if candidate > now:
                    next_run = candidate
                else:
                    next_run = candidate + _datetime_module.timedelta(days=self.interval)
            self.next_run = next_run
            return

        # Weeks with optional start_day (weekday)
        if self.unit == "weeks":
            next_run = now + _datetime_module.timedelta(weeks=self.interval)
            if self.start_day:
                weekday_target = Job.WEEKDAYS.index(self.start_day)
                days_ahead = (weekday_target - now.weekday()) % 7
                # schedule for *this* week only if we haven't run yet
                if days_ahead == 0:
                    if self.last_run is None and (
                        not self.at_time or self.at_time > now.time()
                    ):
                        days_ahead = 0
                    else:
                        days_ahead = 7 * self.interval
                if days_ahead == 0 and self.interval > 1:
                    days_ahead = 7 * self.interval
                candidate = now + _datetime_module.timedelta(days=days_ahead)
                if self.at_time:
                    candidate = candidate.replace(
                        hour=self.at_time.hour,
                        minute=self.at_time.minute,
                        second=self.at_time.second,
                        microsecond=0,
                    )
                    if candidate <= now:
                        candidate += _datetime_module.timedelta(weeks=self.interval)
                next_run = candidate
            self.next_run = next_run
            return

        raise ScheduleError(f"Unsupported time unit {self.unit!r}")

    # --------------------------------------------------------------------- #
    # Job execution helpers
    # --------------------------------------------------------------------- #

    def do(self, job_func: Callable[..., Any], *args: Any, **kwargs: Any) -> "Job":
        """
        Finalise the job specification by registering the callable that should
        be executed when the schedule triggers.
        """
        if not callable(job_func):
            raise ScheduleError("Provided job_func is not callable")
        self.job_func = _functools.partial(job_func, *args, **kwargs)
        self._schedule_next_run()
        return self

    @property
    def should_run(self) -> bool:
        """Return ``True`` if the job should be executed *now*."""
        return (
            self.next_run is not None
            and self.job_func is not None
            and _now() >= self.next_run
        )

    def run(self) -> Any:
        """Run the job and reschedule the next run."""
        if self.job_func is None:
            raise ScheduleError("Job has no function to run")
        self.last_run = _now()
        result = self.job_func()
        # Re-calculate next_run *after* execution
        self._schedule_next_run()
        return result

    # --------------------------------------------------------------------- #
    # Niceties
    # --------------------------------------------------------------------- #

    def __lt__(self, other: "Job"):  # Needed for sorting
        if not isinstance(other, Job):
            return NotImplemented
        # None is always considered after a real datetime
        if self.next_run is None:
            return False
        if other.next_run is None:
            return True
        return self.next_run < other.next_run

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Job (every {self.interval} {self.unit} "
            f"next_run={self.next_run} tags={sorted(self._tags)})>"
        )


# --------------------------------------------------------------------------- #
# Scheduler
# --------------------------------------------------------------------------- #


class Scheduler:
    """
    A scheduler manages multiple ``Job`` instances.  A *global* instance of
    this class is exposed via :pydata:`schedule.default_scheduler`.
    """

    def __init__(self) -> None:
        self.jobs: List[Job] = []

    # --------------------------------------------------------------------- #
    # Job builder
    # --------------------------------------------------------------------- #

    def every(self, interval: int = 1) -> Job:
        job = Job(interval, self)
        self.jobs.append(job)
        return job

    # --------------------------------------------------------------------- #
    # Execution helpers
    # --------------------------------------------------------------------- #

    def run_pending(self) -> int:
        """
        Execute all jobs whose ``next_run`` timestamp is due.  Returns the
        number of jobs that have been executed.
        """
        ran = 0
        # Always sort to ensure deterministic order
        for job in sorted(self.jobs):
            if job.should_run:
                job.run()
                ran += 1
        return ran

    def run_all(self, delay_seconds: float = 0) -> int:
        """
        Run *all* jobs regardless of their schedules.  If ``delay_seconds`` is
        >0 a sleep is inserted between consecutive job executions (useful for
        testing).
        """
        ran = 0
        for job in list(self.jobs):  # copy because jobs reschedule themselves
            job.run()
            ran += 1
            if delay_seconds:
                _sleep(delay_seconds)
        return ran

    # --------------------------------------------------------------------- #
    # Jobs administration
    # --------------------------------------------------------------------- #

    def cancel_job(self, job: Job) -> bool:
        """Remove *job* from this scheduler. Returns ``True`` if removed."""
        try:
            self.jobs.remove(job)
            return True
        except ValueError:
            return False

    def clear(self, *tags: str) -> None:
        """
        Remove jobs.  If *tags* are given, only jobs with at least **one** of
        those tags are removed, otherwise *all* jobs are cleared.
        """
        if not tags:
            self.jobs.clear()
            return
        tags_set = set(tags)
        self.jobs = [j for j in self.jobs if j._tags.isdisjoint(tags_set)]

    def get_jobs(self, tag: Optional[str] = None) -> List[Job]:
        """Return a list of all currently scheduled jobs (optionally filtered by tag)."""
        if tag is None:
            return list(self.jobs)
        return [j for j in self.jobs if tag in j._tags]


# --------------------------------------------------------------------------- #
# Module-level convenience helpers
# --------------------------------------------------------------------------- #

default_scheduler = Scheduler()

# Allow *monkey-patching* in tests:
# schedule.datetime             -> assigns to internal _datetime_module
# schedule.time                 -> same for _time_module
# We mimic this behaviour by providing attribute access fallbacks.


def __getattr__(name: str) -> Any:  # noqa: D401
    if name == "datetime":
        return _datetime_module
    if name == "time":
        return _time_module
    raise AttributeError(name)


# Public proxies
def every(interval: int = 1) -> Job:  # noqa: D401
    return default_scheduler.every(interval)


def run_pending() -> int:
    return default_scheduler.run_pending()


def run_all(delay_seconds: float = 0) -> int:
    return default_scheduler.run_all(delay_seconds)


def clear(*tags: str) -> None:
    return default_scheduler.clear(*tags)


def cancel_job(job: Job) -> bool:
    return default_scheduler.cancel_job(job)