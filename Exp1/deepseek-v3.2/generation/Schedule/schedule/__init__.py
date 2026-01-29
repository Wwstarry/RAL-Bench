"""
Pure Python job scheduling library compatible with the Schedule API.
"""
import time
import datetime
import functools
import threading
from typing import Optional, Callable, Union, List, Any, Dict
import re


class ScheduleError(Exception):
    """Base exception for schedule-related errors."""
    pass


class Job:
    """A periodic job as used by :class:`Scheduler`."""
    
    def __init__(self, interval: int = 1):
        self.interval = interval  # Interval value
        self.unit = None  # seconds, minutes, hours, days, weeks
        self.job_func: Optional[Callable] = None
        self.last_run: Optional[datetime.datetime] = None
        self.next_run: Optional[datetime.datetime] = None
        self.at_time: Optional[datetime.time] = None
        self.start_day: Optional[str] = None  # Monday, Tuesday, etc.
        self.tags = set()
        self.id = None
        self.scheduler: Optional['Scheduler'] = None
        
    def __repr__(self):
        def format_time(t):
            return t.strftime("%Y-%m-%d %H:%M:%S") if t else '[never]'
        
        timer = format_time(self.next_run)
        return f"Job(interval={self.interval}, unit={self.unit}, at={self.at_time}, start_day={self.start_day}, next_run={timer})"
    
    @property
    def second(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        return self.seconds
    
    @property
    def seconds(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        self.unit = 'seconds'
        return self
    
    @property
    def minute(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        return self.minutes
    
    @property
    def minutes(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        self.unit = 'minutes'
        return self
    
    @property
    def hour(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        return self.hours
    
    @property
    def hours(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        self.unit = 'hours'
        return self
    
    @property
    def day(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        return self.days
    
    @property
    def days(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        self.unit = 'days'
        return self
    
    @property
    def week(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        return self.weeks
    
    @property
    def weeks(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        self.unit = 'weeks'
        return self
    
    @property
    def monday(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        self.unit = 'weeks'
        self.start_day = 'monday'
        return self
    
    @property
    def tuesday(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        self.unit = 'weeks'
        self.start_day = 'tuesday'
        return self
    
    @property
    def wednesday(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        self.unit = 'weeks'
        self.start_day = 'wednesday'
        return self
    
    @property
    def thursday(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        self.unit = 'weeks'
        self.start_day = 'thursday'
        return self
    
    @property
    def friday(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        self.unit = 'weeks'
        self.start_day = 'friday'
        return self
    
    @property
    def saturday(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        self.unit = 'weeks'
        self.start_day = 'saturday'
        return self
    
    @property
    def sunday(self):
        if self.unit is not None:
            raise ScheduleError("A unit is already set!")
        self.unit = 'weeks'
        self.start_day = 'sunday'
        return self
    
    def at(self, time_str: str):
        """Schedule the job to run at a specific time each day."""
        if self.unit not in ('days', 'hours', 'weeks') and not self.start_day:
            raise ScheduleError("Invalid unit for at()")
        
        # Parse time string
        if not re.match(r'^\d{1,2}:\d{2}$', time_str):
            raise ScheduleError("Invalid time format, expected HH:MM")
        
        hour, minute = map(int, time_str.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ScheduleError("Invalid time, hour must be 0-23, minute 0-59")
        
        self.at_time = datetime.time(hour, minute)
        return self
    
    def do(self, job_func: Callable, *args, **kwargs):
        """Specify the job function to run."""
        self.job_func = functools.partial(job_func, *args, **kwargs)
        self._schedule_next_run()
        return self
    
    def _schedule_next_run(self, current_time: Optional[datetime.datetime] = None):
        """Schedule the next run time for this job."""
        if current_time is None:
            current_time = datetime.datetime.now()
        
        if self.unit is None:
            raise ScheduleError("Job unit not set")
        
        if self.last_run is None:
            # First run
            self.last_run = current_time
        
        # Calculate next run based on unit
        if self.unit == 'seconds':
            self.next_run = self.last_run + datetime.timedelta(seconds=self.interval)
        
        elif self.unit == 'minutes':
            self.next_run = self.last_run + datetime.timedelta(minutes=self.interval)
        
        elif self.unit == 'hours':
            self.next_run = self.last_run + datetime.timedelta(hours=self.interval)
        
        elif self.unit == 'days':
            if self.at_time is not None:
                # Run at specific time each day
                next_day = self.last_run.date() + datetime.timedelta(days=self.interval)
                self.next_run = datetime.datetime.combine(next_day, self.at_time)
                # If we've already passed that time today, schedule for today
                candidate = datetime.datetime.combine(self.last_run.date(), self.at_time)
                if candidate > self.last_run:
                    self.next_run = candidate
            else:
                self.next_run = self.last_run + datetime.timedelta(days=self.interval)
        
        elif self.unit == 'weeks':
            if self.start_day is not None:
                # Weekly on specific day
                days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                target_day = days.index(self.start_day)
                current_day = current_time.weekday()
                
                days_ahead = target_day - current_day
                if days_ahead <= 0:
                    days_ahead += 7
                
                next_date = current_time.date() + datetime.timedelta(days=days_ahead)
                if self.at_time is not None:
                    self.next_run = datetime.datetime.combine(next_date, self.at_time)
                else:
                    self.next_run = datetime.datetime.combine(next_date, current_time.time())
            else:
                self.next_run = self.last_run + datetime.timedelta(weeks=self.interval)
        
        else:
            raise ScheduleError(f"Unknown unit: {self.unit}")
    
    def run(self):
        """Run the job and schedule the next execution."""
        if self.job_func is None:
            raise ScheduleError("Job function not set")
        
        try:
            self.job_func()
        except Exception:
            # Don't let job exceptions break the scheduler
            pass
        
        self.last_run = datetime.datetime.now()
        self._schedule_next_run()
    
    def should_run(self) -> bool:
        """Return True if the job should be run now."""
        if self.next_run is None:
            return False
        return datetime.datetime.now() >= self.next_run
    
    def tag(self, *tags):
        """Tag the job with one or more tags."""
        self.tags.update(tags)
        return self
    
    def untag(self, *tags):
        """Remove tags from the job."""
        self.tags.difference_update(tags)
        return self


class Scheduler:
    """Job scheduler that manages and runs jobs."""
    
    def __init__(self):
        self.jobs: List[Job] = []
        self._stop_event = threading.Event()
    
    def every(self, interval: int = 1) -> Job:
        """Schedule a new periodic job."""
        job = Job(interval)
        job.scheduler = self
        self.jobs.append(job)
        return job
    
    def run_pending(self):
        """Run all jobs that are scheduled to run."""
        runnable_jobs = [job for job in self.jobs if job.should_run()]
        for job in runnable_jobs:
            job.run()
    
    def run_all(self, delay_seconds: int = 0):
        """Run all jobs regardless of their schedule."""
        for job in self.jobs:
            time.sleep(delay_seconds)
            job.run()
    
    def clear(self, tag: Optional[str] = None):
        """Delete scheduled jobs, optionally filtered by tag."""
        if tag is None:
            self.jobs.clear()
        else:
            self.jobs = [job for job in self.jobs if tag not in job.tags]
    
    def cancel_job(self, job: Job):
        """Remove a specific job from the scheduler."""
        if job in self.jobs:
            self.jobs.remove(job)
    
    def next_run(self):
        """Return the datetime when the next job should run."""
        if not self.jobs:
            return None
        return min(job.next_run for job in self.jobs if job.next_run is not None)
    
    def idle_seconds(self):
        """Return the number of seconds until the next job is scheduled to run."""
        next_run = self.next_run()
        if next_run is None:
            return None
        return (next_run - datetime.datetime.now()).total_seconds()
    
    def get_jobs(self, tag: Optional[str] = None) -> List[Job]:
        """Get all jobs, optionally filtered by tag."""
        if tag is None:
            return self.jobs[:]
        return [job for job in self.jobs if tag in job.tags]
    
    def start(self, interval: float = 1):
        """Start the scheduler in a blocking loop."""
        try:
            while not self._stop_event.is_set():
                self.run_pending()
                time.sleep(interval)
        except KeyboardInterrupt:
            pass
    
    def stop(self):
        """Stop the scheduler loop."""
        self._stop_event.set()


# Create default scheduler instance
default_scheduler = Scheduler()


# Module-level functions that proxy to the default scheduler
def every(interval: int = 1) -> Job:
    """Schedule a new periodic job on the default scheduler."""
    return default_scheduler.every(interval)


def run_pending():
    """Run all pending jobs on the default scheduler."""
    default_scheduler.run_pending()


def run_all(delay_seconds: int = 0):
    """Run all jobs on the default scheduler."""
    default_scheduler.run_all(delay_seconds)


def clear(tag: Optional[str] = None):
    """Clear jobs from the default scheduler."""
    default_scheduler.clear(tag)


def cancel_job(job: Job):
    """Cancel a specific job on the default scheduler."""
    default_scheduler.cancel_job(job)


def next_run():
    """Get the next run time from the default scheduler."""
    return default_scheduler.next_run()


def idle_seconds():
    """Get idle seconds from the default scheduler."""
    return default_scheduler.idle_seconds()


def get_jobs(tag: Optional[str] = None) -> List[Job]:
    """Get jobs from the default scheduler."""
    return default_scheduler.get_jobs(tag)


# Export public API
__all__ = [
    'every',
    'run_pending',
    'run_all',
    'clear',
    'cancel_job',
    'next_run',
    'idle_seconds',
    'get_jobs',
    'Job',
    'Scheduler',
    'ScheduleError'
]