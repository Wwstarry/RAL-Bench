import datetime
import functools
import threading

# Helper to get current time, can be monkeypatched in tests
def _now():
    return datetime.datetime.now()

class Job:
    def __init__(self, interval=1, scheduler=None):
        self.interval = interval
        self.unit = None
        self.at_time = None
        self.latest = None
        self.job_func = None
        self.job_args = ()
        self.job_kwargs = {}
        self.last_run = None
        self.next_run = None
        self.start_day = None
        self.scheduler = scheduler
        self._tag = None
        self._period = None  # Used for hour/minute/second
        self._weekdays = None  # Used for day-of-week jobs

    def __repr__(self):
        return (
            f"<Job: {self.interval} {self.unit}"
            + (f" at {self.at_time}" if self.at_time else "")
            + (f" latest {self.latest}" if self.latest else "")
            + (f" func {self.job_func}" if self.job_func else "")
            + ">"
        )

    def do(self, job_func, *args, **kwargs):
        self.job_func = job_func
        self.job_args = args
        self.job_kwargs = kwargs
        self._schedule_next_run()
        return self

    def _schedule_next_run(self):
        now = self.scheduler._now() if self.scheduler else _now()
        if self.unit == "seconds":
            self.next_run = now + datetime.timedelta(seconds=self.interval)
        elif self.unit == "minutes":
            self.next_run = now + datetime.timedelta(minutes=self.interval)
        elif self.unit == "hours":
            self.next_run = now + datetime.timedelta(hours=self.interval)
        elif self.unit == "days":
            next_run = now + datetime.timedelta(days=self.interval)
            if self.at_time:
                at_time = self._parse_time(self.at_time)
                next_run = next_run.replace(
                    hour=at_time.hour, minute=at_time.minute, second=at_time.second, microsecond=0
                )
                if next_run <= now:
                    next_run += datetime.timedelta(days=1)
            self.next_run = next_run
        elif self.unit == "weeks":
            next_run = now + datetime.timedelta(weeks=self.interval)
            if self.at_time:
                at_time = self._parse_time(self.at_time)
                next_run = next_run.replace(
                    hour=at_time.hour, minute=at_time.minute, second=at_time.second, microsecond=0
                )
                if next_run <= now:
                    next_run += datetime.timedelta(weeks=1)
            self.next_run = next_run
        elif self.unit == "weekday":
            # Find next occurrence of the weekday
            weekday = self._weekdays
            days_ahead = (weekday - now.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            next_run = now + datetime.timedelta(days=days_ahead)
            if self.at_time:
                at_time = self._parse_time(self.at_time)
                next_run = next_run.replace(
                    hour=at_time.hour, minute=at_time.minute, second=at_time.second, microsecond=0
                )
            else:
                next_run = next_run.replace(hour=0, minute=0, second=0, microsecond=0)
            self.next_run = next_run
        else:
            # Not scheduled yet
            self.next_run = None

    def _parse_time(self, time_str):
        # Accept "HH:MM" or "HH:MM:SS"
        parts = [int(p) for p in time_str.split(":")]
        while len(parts) < 3:
            parts.append(0)
        return datetime.time(*parts)

    def at(self, time_str):
        self.at_time = time_str
        self._schedule_next_run()
        return self

    def tag(self, tag):
        self._tag = tag
        return self

    def run(self):
        self.last_run = self.scheduler._now() if self.scheduler else _now()
        ret = self.job_func(*self.job_args, **self.job_kwargs)
        self._schedule_next_run()
        return ret

    def should_run(self):
        now = self.scheduler._now() if self.scheduler else _now()
        return self.next_run is not None and now >= self.next_run

    def cancel(self):
        if self.scheduler:
            self.scheduler.cancel_job(self)

    # For compatibility: allow .monday, .tuesday, etc.
    def _set_weekday(self, weekday):
        self.unit = "weekday"
        self._weekdays = weekday
        self._schedule_next_run()
        return self

    @property
    def monday(self):
        return self._set_weekday(0)

    @property
    def tuesday(self):
        return self._set_weekday(1)

    @property
    def wednesday(self):
        return self._set_weekday(2)

    @property
    def thursday(self):
        return self._set_weekday(3)

    @property
    def friday(self):
        return self._set_weekday(4)

    @property
    def saturday(self):
        return self._set_weekday(5)

    @property
    def sunday(self):
        return self._set_weekday(6)

    @property
    def seconds(self):
        self.unit = "seconds"
        self._schedule_next_run()
        return self

    @property
    def minutes(self):
        self.unit = "minutes"
        self._schedule_next_run()
        return self

    @property
    def hours(self):
        self.unit = "hours"
        self._schedule_next_run()
        return self

    @property
    def days(self):
        self.unit = "days"
        self._schedule_next_run()
        return self

    @property
    def weeks(self):
        self.unit = "weeks"
        self._schedule_next_run()
        return self

    @property
    def day(self):
        self.unit = "days"
        self._schedule_next_run()
        return self

    @property
    def week(self):
        self.unit = "weeks"
        self._schedule_next_run()
        return self

class Scheduler:
    def __init__(self):
        self.jobs = []
        self._now = _now  # Can be monkeypatched for tests

    def every(self, interval=1):
        job = Job(interval=interval, scheduler=self)
        self.jobs.append(job)
        return job

    def run_pending(self):
        runnable_jobs = [job for job in self.jobs if job.should_run()]
        for job in sorted(runnable_jobs, key=lambda j: j.next_run):
            job.run()

    def run_all(self, delay_seconds=0):
        for job in self.jobs:
            job.run()
            if delay_seconds:
                import time
                time.sleep(delay_seconds)

    def cancel_job(self, job):
        try:
            self.jobs.remove(job)
        except ValueError:
            pass

    def clear(self, tag=None):
        if tag is None:
            self.jobs.clear()
        else:
            self.jobs = [job for job in self.jobs if job._tag != tag]

# Top-level singleton scheduler
_default_scheduler = Scheduler()

def every(interval=1):
    return _default_scheduler.every(interval)

def run_pending():
    return _default_scheduler.run_pending()

def run_all(delay_seconds=0):
    return _default_scheduler.run_all(delay_seconds=delay_seconds)

def cancel_job(job):
    return _default_scheduler.cancel_job(job)

def clear(tag=None):
    return _default_scheduler.clear(tag=tag)

__all__ = [
    "every",
    "Job",
    "Scheduler",
    "run_pending",
    "run_all",
    "cancel_job",
    "clear",
]