import datetime
import time
import threading

class Job:
    def __init__(self, interval=1, scheduler=None):
        self.interval = interval
        self.unit = None
        self.at_time = None
        self.job_func = None
        self.last_run = None
        self.next_run = None
        self.scheduler = scheduler
        self._day_of_week = None
        self._unit_seconds = None
        self._tag = None
        self._lock = threading.RLock()

    def __repr__(self):
        return "<Job(interval={}, unit={}, at_time={}, next_run={})>".format(
            self.interval, self.unit, self.at_time, self.next_run
        )

    def _schedule_next_run(self):
        """Calculate the next run datetime based on the interval, unit, and at_time."""
        with self._lock:
            now = self.scheduler.now() if self.scheduler else datetime.datetime.now()
            if self.unit in ("seconds", "second"):
                self._unit_seconds = 1
            elif self.unit in ("minutes", "minute"):
                self._unit_seconds = 60
            elif self.unit in ("hours", "hour"):
                self._unit_seconds = 3600
            elif self.unit in ("days", "day"):
                self._unit_seconds = 86400
            elif self.unit in ("weeks", "week"):
                self._unit_seconds = 604800
            else:
                self._unit_seconds = None

            if self._day_of_week is not None:
                # Schedule for a specific weekday
                days_ahead = (self._day_of_week - now.weekday()) % 7
                if days_ahead == 0:
                    # If today, check if at_time is passed
                    if self.at_time:
                        at_hour, at_minute = self._parse_time(self.at_time)
                        today_run = now.replace(hour=at_hour, minute=at_minute, second=0, microsecond=0)
                        if now >= today_run:
                            days_ahead = 7
                    else:
                        # No at_time, so run today if time not passed
                        if self.next_run and now >= self.next_run:
                            days_ahead = 7
                next_run_date = now + datetime.timedelta(days=days_ahead)
                if self.at_time:
                    at_hour, at_minute = self._parse_time(self.at_time)
                    self.next_run = next_run_date.replace(hour=at_hour, minute=at_minute, second=0, microsecond=0)
                else:
                    # Run at the same time as last run or now
                    if self.next_run:
                        self.next_run = self.next_run + datetime.timedelta(weeks=self.interval)
                    else:
                        self.next_run = next_run_date.replace(hour=now.hour, minute=now.minute, second=now.second, microsecond=0)
                if self.next_run <= now:
                    self.next_run += datetime.timedelta(weeks=self.interval)
            elif self.unit in ("days", "day") and self.at_time:
                at_hour, at_minute = self._parse_time(self.at_time)
                next_run_date = now.date()
                candidate = datetime.datetime.combine(next_run_date, datetime.time(at_hour, at_minute))
                if self.next_run is None or candidate <= now:
                    candidate += datetime.timedelta(days=self.interval)
                self.next_run = candidate
            elif self.unit in ("hours", "hour") and self.at_time:
                # at_time ignored for hours in reference schedule, but we support it by scheduling at that minute
                at_hour, at_minute = self._parse_time(self.at_time)
                candidate = now.replace(minute=at_minute, second=0, microsecond=0)
                if candidate <= now:
                    candidate += datetime.timedelta(hours=self.interval)
                self.next_run = candidate
            elif self._unit_seconds is not None:
                if self.next_run is None:
                    self.next_run = now + datetime.timedelta(seconds=self.interval * self._unit_seconds)
                else:
                    self.next_run += datetime.timedelta(seconds=self.interval * self._unit_seconds)
            else:
                # fallback: run immediately
                self.next_run = now

    def _parse_time(self, time_str):
        # time_str is "HH:MM"
        parts = time_str.split(":")
        if len(parts) != 2:
            raise ValueError("Invalid time format, expected HH:MM")
        hour = int(parts[0])
        minute = int(parts[1])
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError("Invalid time value")
        return hour, minute

    def do(self, job_func, *args, **kwargs):
        self.job_func = lambda: job_func(*args, **kwargs)
        if self.scheduler:
            self._schedule_next_run()
            self.scheduler._jobs.append(self)
        return self

    def at(self, time_str):
        self.at_time = time_str
        if self.scheduler:
            self._schedule_next_run()
        return self

    def run(self):
        if self.job_func is None:
            return None
        ret = self.job_func()
        self.last_run = self.scheduler.now() if self.scheduler else datetime.datetime.now()
        self._schedule_next_run()
        return ret

    def should_run(self):
        now = self.scheduler.now() if self.scheduler else datetime.datetime.now()
        return self.next_run is not None and now >= self.next_run

    def every(self, interval=1):
        self.interval = interval
        if self.scheduler:
            self._schedule_next_run()
        return self

    # Properties for time units
    @property
    def seconds(self):
        self.unit = "seconds"
        if self.scheduler:
            self._schedule_next_run()
        return self

    @property
    def second(self):
        return self.seconds

    @property
    def minutes(self):
        self.unit = "minutes"
        if self.scheduler:
            self._schedule_next_run()
        return self

    @property
    def minute(self):
        return self.minutes

    @property
    def hours(self):
        self.unit = "hours"
        if self.scheduler:
            self._schedule_next_run()
        return self

    @property
    def hour(self):
        return self.hours

    @property
    def days(self):
        self.unit = "days"
        if self.scheduler:
            self._schedule_next_run()
        return self

    @property
    def day(self):
        return self.days

    @property
    def weeks(self):
        self.unit = "weeks"
        if self.scheduler:
            self._schedule_next_run()
        return self

    @property
    def week(self):
        return self.weeks

    # Weekdays
    @property
    def monday(self):
        self.unit = "days"
        self._day_of_week = 0
        if self.scheduler:
            self._schedule_next_run()
        return self

    @property
    def tuesday(self):
        self.unit = "days"
        self._day_of_week = 1
        if self.scheduler:
            self._schedule_next_run()
        return self

    @property
    def wednesday(self):
        self.unit = "days"
        self._day_of_week = 2
        if self.scheduler:
            self._schedule_next_run()
        return self

    @property
    def thursday(self):
        self.unit = "days"
        self._day_of_week = 3
        if self.scheduler:
            self._schedule_next_run()
        return self

    @property
    def friday(self):
        self.unit = "days"
        self._day_of_week = 4
        if self.scheduler:
            self._schedule_next_run()
        return self

    @property
    def saturday(self):
        self.unit = "days"
        self._day_of_week = 5
        if self.scheduler:
            self._schedule_next_run()
        return self

    @property
    def sunday(self):
        self.unit = "days"
        self._day_of_week = 6
        if self.scheduler:
            self._schedule_next_run()
        return self


class Scheduler:
    def __init__(self):
        self._jobs = []
        self._lock = threading.RLock()

    def now(self):
        # This method can be monkeypatched for time mocking in tests
        return datetime.datetime.now()

    def every(self, interval=1):
        job = Job(interval=interval, scheduler=self)
        return job

    def run_pending(self):
        """Run all jobs that are scheduled to run."""
        with self._lock:
            runnable_jobs = [job for job in self._jobs if job.should_run()]
            for job in sorted(runnable_jobs, key=lambda j: j.next_run):
                job.run()

    def run_all(self, delay_seconds=0):
        """Run all jobs regardless of their scheduled time."""
        with self._lock:
            for job in self._jobs:
                job.run()
                if delay_seconds > 0:
                    time.sleep(delay_seconds)

    def clear(self):
        with self._lock:
            self._jobs.clear()

    def get_jobs(self):
        with self._lock:
            return list(self._jobs)


# Top-level module API
_scheduler = Scheduler()

def every(interval=1):
    return _scheduler.every(interval)

Job = Job
Scheduler = Scheduler
schedule = _scheduler