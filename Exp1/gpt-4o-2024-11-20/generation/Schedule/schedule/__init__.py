import datetime
import time
import functools
from threading import Event, Thread


class Job:
    def __init__(self, interval, scheduler=None):
        self.interval = interval
        self.unit = None
        self.at_time = None
        self.last_run = None
        self.next_run = None
        self.job_func = None
        self.scheduler = scheduler
        self.start_day = None

    def __repr__(self):
        return f"Job(interval={self.interval}, unit={self.unit}, at_time={self.at_time})"

    def at(self, time_str):
        if self.unit not in ("days", "day"):
            raise ValueError("`at` is only valid for daily jobs")
        hour, minute = map(int, time_str.split(":"))
        self.at_time = datetime.time(hour, minute)
        return self

    def do(self, job_func, *args, **kwargs):
        self.job_func = functools.partial(job_func, *args, **kwargs)
        self._schedule_next_run()
        return self

    def _schedule_next_run(self):
        now = datetime.datetime.now()
        if self.unit == "seconds":
            self.next_run = now + datetime.timedelta(seconds=self.interval)
        elif self.unit == "minutes":
            self.next_run = now + datetime.timedelta(minutes=self.interval)
        elif self.unit == "hours":
            self.next_run = now + datetime.timedelta(hours=self.interval)
        elif self.unit in ("days", "day"):
            self.next_run = now + datetime.timedelta(days=self.interval)
            if self.at_time:
                self.next_run = self.next_run.replace(
                    hour=self.at_time.hour, minute=self.at_time.minute, second=0, microsecond=0
                )
                if self.next_run <= now:
                    self.next_run += datetime.timedelta(days=1)
        elif self.unit == "weeks":
            self.next_run = now + datetime.timedelta(weeks=self.interval)
        else:
            raise ValueError("Invalid time unit")
        self.last_run = None

    def run(self):
        if self.job_func is None:
            raise RuntimeError("Job function not assigned")
        self.last_run = datetime.datetime.now()
        self.job_func()
        self._schedule_next_run()


class Scheduler:
    def __init__(self):
        self.jobs = []

    def every(self, interval=1):
        job = Job(interval, scheduler=self)
        self.jobs.append(job)
        return job

    def run_pending(self):
        now = datetime.datetime.now()
        for job in sorted(self.jobs, key=lambda j: j.next_run):
            if job.next_run and job.next_run <= now:
                job.run()

    def run_all(self, delay_seconds=0):
        for job in self.jobs:
            job.run()
            if delay_seconds > 0:
                time.sleep(delay_seconds)

    def clear(self):
        self.jobs.clear()

    def cancel_job(self, job):
        self.jobs.remove(job)


class Every:
    def __init__(self, scheduler, interval):
        self.scheduler = scheduler
        self.interval = interval

    @property
    def seconds(self):
        job = self.scheduler.every(self.interval)
        job.unit = "seconds"
        return job

    @property
    def minutes(self):
        job = self.scheduler.every(self.interval)
        job.unit = "minutes"
        return job

    @property
    def hours(self):
        job = self.scheduler.every(self.interval)
        job.unit = "hours"
        return job

    @property
    def days(self):
        job = self.scheduler.every(self.interval)
        job.unit = "days"
        return job

    @property
    def weeks(self):
        job = self.scheduler.every(self.interval)
        job.unit = "weeks"
        return job

    @property
    def monday(self):
        return self._weekday(0)

    @property
    def tuesday(self):
        return self._weekday(1)

    @property
    def wednesday(self):
        return self._weekday(2)

    @property
    def thursday(self):
        return self._weekday(3)

    @property
    def friday(self):
        return self._weekday(4)

    @property
    def saturday(self):
        return self._weekday(5)

    @property
    def sunday(self):
        return self._weekday(6)

    def _weekday(self, day):
        job = self.scheduler.every(self.interval)
        job.unit = "days"
        job.start_day = day
        return job


class Schedule:
    def __init__(self):
        self.scheduler = Scheduler()

    def every(self, interval=1):
        return Every(self.scheduler, interval)

    def run_pending(self):
        self.scheduler.run_pending()

    def run_all(self, delay_seconds=0):
        self.scheduler.run_all(delay_seconds)

    def clear(self):
        self.scheduler.clear()

    def cancel_job(self, job):
        self.scheduler.cancel_job(job)


schedule = Schedule()