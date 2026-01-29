"""
A pure Python job scheduling library that is API-compatible with the core parts of
the reference "Schedule" project.

Provides:
    - schedule.every
    - Job class
    - Scheduler class

Usage examples:
    import schedule

    def job():
        print("I'm working...")

    schedule.every(10).seconds.do(job)
    schedule.every().day.at("10:30").do(job)
    schedule.every().monday.do(job)

    while True:
        schedule.run_pending()
"""

import datetime
import time
import functools

# List of weekdays in Python's datetime format (Monday=0, Sunday=6)
WEEKDAYS = {
    'monday': 0,
    'tuesday': 1,
    'wednesday': 2,
    'thursday': 3,
    'friday': 4,
    'saturday': 5,
    'sunday': 6,
}


class ScheduleError(Exception):
    """Base schedule exception."""
    pass


class CancelJob(object):
    """
    Can be returned from a job to indicate that the job should be canceled.
    """
    pass


def _round_time(dt, seconds=1):
    """
    Rounds a naive datetime object down to a multiple of seconds.
    """
    new_timestamp = (int(dt.timestamp()) // seconds) * seconds
    return datetime.datetime.fromtimestamp(new_timestamp)


def _set_time_of_day(dt, time_obj):
    """Set the time of day for a datetime object."""
    return dt.replace(hour=time_obj.hour, minute=time_obj.minute,
                      second=time_obj.second, microsecond=0)


class Job(object):
    """
    Represents a scheduled job. A Job is used to schedule a call to a job function.
    """

    def __init__(self, interval, scheduler=None):
        self.interval = interval  # Default scheduling interval
        self.unit = None
        self.do_func = None
        self.job_func = None
        self.next_run = None
        self.last_run = None
        self.start_day = None
        self.at_time = None
        self.scheduler = scheduler
        self.tags = set()
        self._period = None  # 'seconds', 'minutes', 'hours', 'days', 'weeks'
        self._time_type = None  # 'at', 'day_of_week', etc.
        self._week_day = None

    def do(self, job_func, *args, **kwargs):
        """
        Assign the job_func to be called. Returns the Job itself.
        """
        self.job_func = functools.partial(job_func, *args, **kwargs)
        self.do_func = job_func  # Keep reference to original for introspection
        self._schedule_next_run()
        if self.scheduler is not None:
            self.scheduler.jobs.append(self)
        return self

    def _schedule_next_run(self):
        """
        Compute the next run time for this job.
        """
        if self.unit not in ("seconds", "minutes", "hours", "days", "weeks"):
            raise ScheduleError("Invalid unit (valid units are 'seconds', 'minutes', 'hours', 'days', 'weeks')")
        if self.last_run is None:
            # Start from now for the first scheduling
            now = self._now()
        else:
            now = self.last_run

        if self.unit == 'seconds':
            next_time = now + datetime.timedelta(seconds=self.interval)
        elif self.unit == 'minutes':
            next_time = now + datetime.timedelta(minutes=self.interval)
        elif self.unit == 'hours':
            next_time = now + datetime.timedelta(hours=self.interval)
        elif self.unit == 'days':
            next_time = now + datetime.timedelta(days=self.interval)
            if self.at_time is not None:
                # If we have an at_time, set it
                potential_next = _set_time_of_day(next_time, self.at_time)
                # If it is in the past, use the next day
                if potential_next <= now:
                    potential_next += datetime.timedelta(days=self.interval)
                next_time = potential_next
        elif self.unit == 'weeks':
            days = self.interval * 7
            next_time = now + datetime.timedelta(days=days)
            if self.start_day is not None:
                # We have a weekday start
                weekday = WEEKDAYS[self.start_day]
                # Move forward to that weekday
                while next_time.weekday() != weekday:
                    next_time += datetime.timedelta(days=1)
            if self.at_time is not None:
                potential_next = _set_time_of_day(next_time, self.at_time)
                if potential_next <= now:
                    # Bump one more week
                    potential_next += datetime.timedelta(days=7)
                next_time = potential_next

        self.next_run = next_time

    def run(self):
        """
        Run the job and immediately reschedule it.
        If the job function returns CancelJob, the job is canceled.
        """
        self.last_run = self._now()
        result = self.job_func()
        if result is CancelJob:
            return CancelJob
        self._schedule_next_run()
        return result

    def second(self):
        return self.seconds

    @property
    def seconds(self):
        self.unit = 'seconds'
        return self

    @property
    def minutes(self):
        self.unit = 'minutes'
        return self

    @property
    def hours(self):
        self.unit = 'hours'
        return self

    @property
    def day(self):
        self.unit = 'days'
        return self

    def at(self, time_str):
        """
        Schedule the job at a specific time of day for 'days' or 'weeks' units.
        """
        if self.unit not in ('days', 'weeks'):
            raise ScheduleError("Invalid 'at' used for unit " + str(self.unit))
        hour, minute = [int(t) for t in time_str.split(':')]
        self.at_time = datetime.time(hour, minute)
        return self

    @property
    def monday(self):
        return self._week_day('monday')

    @property
    def tuesday(self):
        return self._week_day('tuesday')

    @property
    def wednesday(self):
        return self._week_day('wednesday')

    @property
    def thursday(self):
        return self._week_day('thursday')

    @property
    def friday(self):
        return self._week_day('friday')

    @property
    def saturday(self):
        return self._week_day('saturday')

    @property
    def sunday(self):
        return self._week_day('sunday')

    def _week_day(self, dayname):
        """
        Sets this job to execute on a particular day of the week.
        """
        self.unit = 'weeks'
        self.start_day = dayname
        return self

    def _now(self):
        """
        Returns current local datetime, used in job scheduling. 
        This function can be monkeypatched in tests for deterministic runs.
        """
        return datetime.datetime.now()


class Scheduler(object):
    """
    The Scheduler class, which keeps a list of jobs and can run them.
    """

    def __init__(self):
        self.jobs = []

    def now(self):
        """
        Return the current local datetime. 
        May be monkeypatched for deterministic tests.
        """
        return datetime.datetime.now()

    def every(self, interval=1):
        """
        Schedule a new job.
        """
        job = Job(interval, self)
        return job

    def run_pending(self):
        """
        Run all jobs that are scheduled to run at the current time.
        """
        runnable_jobs = (job for job in self.jobs if job.next_run is not None and job.next_run <= self.now())
        for job in sorted(runnable_jobs, key=lambda j: j.next_run):
            result = job.run()
            if result is CancelJob:
                self.cancel_job(job)

    def run_all(self, delay_seconds=0):
        """
        Run all jobs regardless of their scheduled time.
        delay_seconds: wait this long between each job
        """
        for job in list(self.jobs):
            result = job.run()
            if result is CancelJob:
                self.cancel_job(job)
            if delay_seconds > 0:
                time.sleep(delay_seconds)

    def get_jobs(self, tag=None):
        """
        Return a list of scheduled jobs.
        If tag is specified, only return jobs with that tag.
        """
        if tag is None:
            return self.jobs[:]
        else:
            return [job for job in self.jobs if tag in job.tags]

    def cancel_job(self, job):
        """
        Delete a scheduled job.
        """
        if job in self.jobs:
            self.jobs.remove(job)

    def clear(self, tag=None):
        """
        Delete all scheduled jobs. If tag is specified, only clear jobs with that tag.
        """
        if tag is None:
            del self.jobs[:]
        else:
            self.jobs = [job for job in self.jobs if tag not in job.tags]


#: The default scheduler instance
_default_scheduler = Scheduler()

def every(interval=1):
    """
    Schedule a new job using the default scheduler.
    """
    return _default_scheduler.every(interval)

def run_pending():
    """
    Run all jobs that are scheduled to run at this time using the default scheduler.
    """
    _default_scheduler.run_pending()

def run_all(delay_seconds=0):
    """
    Run all jobs regardless of their scheduled time, using the default scheduler.
    """
    _default_scheduler.run_all(delay_seconds)