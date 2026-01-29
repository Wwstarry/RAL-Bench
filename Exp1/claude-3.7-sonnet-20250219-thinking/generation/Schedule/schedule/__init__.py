import datetime
import functools
import logging
import time
from typing import Any, Callable, List, Optional, Set, Union

logger = logging.getLogger('schedule')

# Constants
MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = range(7)


class Job:
    """
    A periodic job as used by `Scheduler`.
    """
    def __init__(self, interval: int, scheduler: Optional['Scheduler'] = None) -> None:
        self.interval = interval
        self.job_func = None
        self.last_run = None
        self.next_run = None
        self.unit = None
        self.at_time = None
        self.start_day = None
        self.tags: Set[str] = set()
        self.scheduler = scheduler if scheduler is not None else default_scheduler

    def __call__(self, *args, **kwargs) -> Any:
        """Call the job function"""
        if self.job_func is not None:
            return self.job_func(*args, **kwargs)
        return None

    def __repr__(self) -> str:
        def format_time(t):
            return t.strftime("%Y-%m-%d %H:%M:%S") if t else '[never]'

        status = 'next run at: %s' % format_time(self.next_run)
        if self.last_run:
            status += ', last run at: %s' % format_time(self.last_run)

        if self.job_func:
            job_func_name = getattr(self.job_func, "__name__", repr(self.job_func))
            job_name = job_func_name
        else:
            job_name = "[no job function]"

        return "Job(%s, %s)" % (job_name, status)

    def _schedule_next_run(self) -> None:
        """Calculate the next run time based on the job's unit and interval"""
        if self.unit is None:
            return

        now = datetime.datetime.now()
        
        if self.unit == 'days' and self.at_time is not None:
            # Daily job at specific time
            hour, minute = self.at_time.hour, self.at_time.minute
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += datetime.timedelta(days=self.interval)
            self.next_run = next_run
        elif self.unit == 'weeks' and self.start_day is not None:
            # Weekly job on specific day
            days_ahead = self.start_day - now.weekday()
            if days_ahead < 0:
                days_ahead += 7
            elif days_ahead == 0 and now.time() > self.at_time if self.at_time else datetime.time(0, 0):
                days_ahead = 7
                
            next_run = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=days_ahead)
            if self.at_time is not None:
                next_run = next_run.replace(hour=self.at_time.hour, minute=self.at_time.minute)
            self.next_run = next_run
        else:
            # Simple interval-based scheduling
            if self.last_run is None:
                self.next_run = now
            else:
                interval_delta = None
                if self.unit == 'seconds':
                    interval_delta = datetime.timedelta(seconds=self.interval)
                elif self.unit == 'minutes':
                    interval_delta = datetime.timedelta(minutes=self.interval)
                elif self.unit == 'hours':
                    interval_delta = datetime.timedelta(hours=self.interval)
                elif self.unit == 'days':
                    interval_delta = datetime.timedelta(days=self.interval)
                elif self.unit == 'weeks':
                    interval_delta = datetime.timedelta(weeks=self.interval)
                
                if interval_delta:
                    self.next_run = self.last_run + interval_delta
                    if self.next_run <= now:
                        # If we've missed runs, skip ahead to the next one
                        time_since_last_run = now - self.last_run
                        missed_runs = time_since_last_run // interval_delta
                        self.next_run = self.last_run + interval_delta * (missed_runs + 1)

    def do(self, job_func: Callable, *args, **kwargs) -> 'Job':
        """Specify the job action"""
        self.job_func = functools.partial(job_func, *args, **kwargs)
        try:
            functools.update_wrapper(self.job_func, job_func)
        except AttributeError:
            # job_funcs already wrapped by functools.partial won't have
            # __name__, __module__ or __doc__ attributes
            pass
        self._schedule_next_run()
        return self

    def run(self) -> 'Job':
        """Run the job and reschedule it"""
        logger.debug('Running job %s', self)
        self.last_run = datetime.datetime.now()
        self._schedule_next_run()
        self()
        return self

    def should_run(self) -> bool:
        """Return True if the job should run now"""
        return self.next_run is not None and datetime.datetime.now() >= self.next_run

    def seconds(self) -> 'Job':
        """Schedule job to run every N seconds"""
        self.unit = 'seconds'
        self._schedule_next_run()
        return self

    def minutes(self) -> 'Job':
        """Schedule job to run every N minutes"""
        self.unit = 'minutes'
        self._schedule_next_run()
        return self

    def hours(self) -> 'Job':
        """Schedule job to run every N hours"""
        self.unit = 'hours'
        self._schedule_next_run()
        return self

    def day(self) -> 'Job':
        """Schedule job to run every day"""
        self.interval = 1
        self.unit = 'days'
        self._schedule_next_run()
        return self

    def days(self) -> 'Job':
        """Schedule job to run every N days"""
        self.unit = 'days'
        self._schedule_next_run()
        return self

    def week(self) -> 'Job':
        """Schedule job to run every week"""
        self.interval = 1
        self.unit = 'weeks'
        self._schedule_next_run()
        return self

    def weeks(self) -> 'Job':
        """Schedule job to run every N weeks"""
        self.unit = 'weeks'
        self._schedule_next_run()
        return self

    def monday(self) -> 'Job':
        """Schedule job to run every Monday"""
        self.start_day = MONDAY
        self.interval = 1
        self.unit = 'weeks'
        self._schedule_next_run()
        return self

    def tuesday(self) -> 'Job':
        """Schedule job to run every Tuesday"""
        self.start_day = TUESDAY
        self.interval = 1
        self.unit = 'weeks'
        self._schedule_next_run()
        return self

    def wednesday(self) -> 'Job':
        """Schedule job to run every Wednesday"""
        self.start_day = WEDNESDAY
        self.interval = 1
        self.unit = 'weeks'
        self._schedule_next_run()
        return self

    def thursday(self) -> 'Job':
        """Schedule job to run every Thursday"""
        self.start_day = THURSDAY
        self.interval = 1
        self.unit = 'weeks'
        self._schedule_next_run()
        return self

    def friday(self) -> 'Job':
        """Schedule job to run every Friday"""
        self.start_day = FRIDAY
        self.interval = 1
        self.unit = 'weeks'
        self._schedule_next_run()
        return self

    def saturday(self) -> 'Job':
        """Schedule job to run every Saturday"""
        self.start_day = SATURDAY
        self.interval = 1
        self.unit = 'weeks'
        self._schedule_next_run()
        return self

    def sunday(self) -> 'Job':
        """Schedule job to run every Sunday"""
        self.start_day = SUNDAY
        self.interval = 1
        self.unit = 'weeks'
        self._schedule_next_run()
        return self

    def at(self, time_str: str) -> 'Job':
        """Schedule the job to run at a specific time"""
        if self.unit not in ('days', 'weeks'):
            raise TypeError("at() should be used with daily or weekly jobs")
        
        try:
            hour, minute = time_str.split(':')
            hour, minute = int(hour), int(minute)
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
            self.at_time = datetime.time(hour=hour, minute=minute)
        except (ValueError, TypeError):
            raise ValueError("Invalid time format. Expected 'HH:MM' format")
        
        self._schedule_next_run()
        return self

    def tag(self, *tags: str) -> 'Job':
        """Add tags to the job"""
        if not all(isinstance(tag, str) for tag in tags):
            raise TypeError('Tags must be strings')
        self.tags.update(tags)
        return self


class Scheduler:
    """
    Responsible for scheduling and running jobs.
    """
    def __init__(self) -> None:
        self.jobs: List[Job] = []
    
    def every(self, interval: int = 1) -> Job:
        """Schedule a new periodic job"""
        job = Job(interval, scheduler=self)
        self.jobs.append(job)
        return job
    
    def run_pending(self) -> None:
        """Run all jobs that are scheduled to run"""
        runnable_jobs = [job for job in self.jobs if job.should_run()]
        for job in sorted(runnable_jobs, key=lambda j: j.next_run):
            job.run()
    
    def run_all(self, delay_seconds: int = 0) -> None:
        """Run all jobs regardless of whether they are scheduled to run or not"""
        for job in self.jobs:
            job.run()
            if delay_seconds > 0:
                time.sleep(delay_seconds)
    
    def clear(self, tag: Optional[str] = None) -> None:
        """Delete jobs, optionally filtering by tag"""
        if tag is None:
            self.jobs = []
        else:
            self.jobs = [job for job in self.jobs if tag not in job.tags]
    
    def cancel_job(self, job: Job) -> None:
        """Delete a specific job from the scheduler"""
        try:
            self.jobs.remove(job)
        except ValueError:
            pass


# Create a default scheduler instance
default_scheduler = Scheduler()

# Expose the default scheduler's methods
every = default_scheduler.every
run_pending = default_scheduler.run_pending
run_all = default_scheduler.run_all
clear = default_scheduler.clear