"""
A pure Python job scheduling library.
"""

import datetime
import time
import re
from typing import Optional, Callable, Union, List, Any


class CancelJob(object):
    """Can be returned from a job to unschedule itself."""
    pass


class Job:
    """A scheduled job that encapsulates a job function and its schedule."""
    
    def __init__(self, interval: int, scheduler: Optional['Scheduler'] = None):
        self.interval = interval
        self.scheduler = scheduler
        self.job_func: Optional[Callable] = None
        self.unit: Optional[str] = None
        self.at_time: Optional[datetime.time] = None
        self.latest: Optional[int] = None
        self.next_run: Optional[datetime.datetime] = None
        self.period: Optional[datetime.timedelta] = None
        self.start_day: Optional[int] = None
        self.tags: set = set()
        self.cancel_after: Optional[datetime.datetime] = None
        
    def do(self, job_func: Callable, *args, **kwargs) -> 'Job':
        """Schedule this job to run job_func with the given arguments."""
        self.job_func = job_func
        self.job_func_args = args
        self.job_func_kwargs = kwargs
        self._schedule_next_run()
        if self.scheduler is None:
            raise RuntimeError("Job is not associated with a scheduler")
        self.scheduler.jobs.append(self)
        return self
    
    def run(self) -> Any:
        """Run this job."""
        ret = self.job_func(*self.job_func_args, **self.job_func_kwargs)
        return ret
    
    def should_run(self) -> bool:
        """True if this job should be run now."""
        return datetime.datetime.now() >= self.next_run
    
    def _schedule_next_run(self) -> None:
        """Calculate the next run time for this job."""
        if self.unit not in ('seconds', 'minutes', 'hours', 'days', 'weeks',
                             'monday', 'tuesday', 'wednesday', 'thursday',
                             'friday', 'saturday', 'sunday'):
            raise ValueError(f'Invalid time unit: {self.unit}')
        
        if self.unit == 'seconds':
            self.period = datetime.timedelta(seconds=self.interval)
        elif self.unit == 'minutes':
            self.period = datetime.timedelta(minutes=self.interval)
        elif self.unit == 'hours':
            self.period = datetime.timedelta(hours=self.interval)
        elif self.unit == 'days':
            self.period = datetime.timedelta(days=self.interval)
        elif self.unit == 'weeks':
            self.period = datetime.timedelta(weeks=self.interval)
        else:
            # Weekday
            weekdays = ['monday', 'tuesday', 'wednesday', 'thursday',
                       'friday', 'saturday', 'sunday']
            self.start_day = weekdays.index(self.unit)
            self.period = datetime.timedelta(weeks=self.interval)
        
        self.next_run = self._calculate_next_run()
    
    def _calculate_next_run(self) -> datetime.datetime:
        """Calculate when this job should run next."""
        now = datetime.datetime.now()
        
        if self.unit in ('seconds', 'minutes', 'hours'):
            if self.latest is not None:
                import random
                interval_seconds = self.period.total_seconds()
                latest_seconds = self.latest
                random_seconds = random.randint(int(interval_seconds), latest_seconds)
                return now + datetime.timedelta(seconds=random_seconds)
            return now + self.period
        
        if self.unit == 'days':
            if self.at_time is not None:
                next_run = now.replace(hour=self.at_time.hour,
                                      minute=self.at_time.minute,
                                      second=self.at_time.second,
                                      microsecond=0)
                if next_run <= now:
                    next_run += datetime.timedelta(days=self.interval)
                return next_run
            else:
                if self.latest is not None:
                    import random
                    interval_seconds = self.period.total_seconds()
                    latest_seconds = self.latest
                    random_seconds = random.randint(int(interval_seconds), latest_seconds)
                    return now + datetime.timedelta(seconds=random_seconds)
                return now + self.period
        
        if self.unit == 'weeks':
            if self.at_time is not None:
                next_run = now.replace(hour=self.at_time.hour,
                                      minute=self.at_time.minute,
                                      second=self.at_time.second,
                                      microsecond=0)
                days_ahead = 7 * self.interval
                if next_run <= now:
                    next_run += datetime.timedelta(days=days_ahead)
                return next_run
            else:
                return now + self.period
        
        # Weekday scheduling
        if self.start_day is not None:
            weekday = now.weekday()
            days_ahead = (self.start_day - weekday) % 7
            
            if self.at_time is not None:
                next_run = now.replace(hour=self.at_time.hour,
                                      minute=self.at_time.minute,
                                      second=self.at_time.second,
                                      microsecond=0)
                next_run += datetime.timedelta(days=days_ahead)
                
                if next_run <= now:
                    next_run += datetime.timedelta(weeks=self.interval)
                return next_run
            else:
                if days_ahead == 0:
                    days_ahead = 7 * self.interval
                return now + datetime.timedelta(days=days_ahead)
        
        return now + self.period
    
    @property
    def second(self) -> 'Job':
        """Schedule the job every second."""
        if self.interval != 1:
            raise ValueError('Use seconds instead of second')
        return self.seconds
    
    @property
    def seconds(self) -> 'Job':
        """Schedule the job every n seconds."""
        self.unit = 'seconds'
        return self
    
    @property
    def minute(self) -> 'Job':
        """Schedule the job every minute."""
        if self.interval != 1:
            raise ValueError('Use minutes instead of minute')
        return self.minutes
    
    @property
    def minutes(self) -> 'Job':
        """Schedule the job every n minutes."""
        self.unit = 'minutes'
        return self
    
    @property
    def hour(self) -> 'Job':
        """Schedule the job every hour."""
        if self.interval != 1:
            raise ValueError('Use hours instead of hour')
        return self.hours
    
    @property
    def hours(self) -> 'Job':
        """Schedule the job every n hours."""
        self.unit = 'hours'
        return self
    
    @property
    def day(self) -> 'Job':
        """Schedule the job every day."""
        if self.interval != 1:
            raise ValueError('Use days instead of day')
        return self.days
    
    @property
    def days(self) -> 'Job':
        """Schedule the job every n days."""
        self.unit = 'days'
        return self
    
    @property
    def week(self) -> 'Job':
        """Schedule the job every week."""
        if self.interval != 1:
            raise ValueError('Use weeks instead of week')
        return self.weeks
    
    @property
    def weeks(self) -> 'Job':
        """Schedule the job every n weeks."""
        self.unit = 'weeks'
        return self
    
    @property
    def monday(self) -> 'Job':
        """Schedule the job every Monday."""
        self.unit = 'monday'
        return self
    
    @property
    def tuesday(self) -> 'Job':
        """Schedule the job every Tuesday."""
        self.unit = 'tuesday'
        return self
    
    @property
    def wednesday(self) -> 'Job':
        """Schedule the job every Wednesday."""
        self.unit = 'wednesday'
        return self
    
    @property
    def thursday(self) -> 'Job':
        """Schedule the job every Thursday."""
        self.unit = 'thursday'
        return self
    
    @property
    def friday(self) -> 'Job':
        """Schedule the job every Friday."""
        self.unit = 'friday'
        return self
    
    @property
    def saturday(self) -> 'Job':
        """Schedule the job every Saturday."""
        self.unit = 'saturday'
        return self
    
    @property
    def sunday(self) -> 'Job':
        """Schedule the job every Sunday."""
        self.unit = 'sunday'
        return self
    
    def at(self, time_str: str) -> 'Job':
        """Schedule the job to run at a specific time of day."""
        time_parts = time_str.split(':')
        if len(time_parts) == 2:
            hour, minute = int(time_parts[0]), int(time_parts[1])
            second = 0
        elif len(time_parts) == 3:
            hour, minute, second = int(time_parts[0]), int(time_parts[1]), int(time_parts[2])
        else:
            raise ValueError(f'Invalid time format: {time_str}')
        
        self.at_time = datetime.time(hour, minute, second)
        return self
    
    def to(self, latest: int) -> 'Job':
        """Schedule the job to run at random intervals between interval and latest."""
        self.latest = latest
        return self
    
    def tag(self, *tags: str) -> 'Job':
        """Tag the job with one or more unique identifiers."""
        self.tags.update(tags)
        return self
    
    def until(self, until_time: Union[datetime.datetime, datetime.timedelta, datetime.time, str]) -> 'Job':
        """Schedule the job until a certain time."""
        if isinstance(until_time, datetime.datetime):
            self.cancel_after = until_time
        elif isinstance(until_time, datetime.timedelta):
            self.cancel_after = datetime.datetime.now() + until_time
        elif isinstance(until_time, datetime.time):
            now = datetime.datetime.now()
            cancel_at = now.replace(hour=until_time.hour,
                                   minute=until_time.minute,
                                   second=until_time.second,
                                   microsecond=0)
            if cancel_at <= now:
                cancel_at += datetime.timedelta(days=1)
            self.cancel_after = cancel_at
        elif isinstance(until_time, str):
            time_parts = until_time.split(':')
            if len(time_parts) == 2:
                hour, minute = int(time_parts[0]), int(time_parts[1])
                second = 0
            elif len(time_parts) == 3:
                hour, minute, second = int(time_parts[0]), int(time_parts[1]), int(time_parts[2])
            else:
                raise ValueError(f'Invalid time format: {until_time}')
            
            now = datetime.datetime.now()
            cancel_at = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
            if cancel_at <= now:
                cancel_at += datetime.timedelta(days=1)
            self.cancel_after = cancel_at
        return self


class Scheduler:
    """A job scheduler."""
    
    def __init__(self):
        self.jobs: List[Job] = []
    
    def every(self, interval: int = 1) -> Job:
        """Create a new job with the given interval."""
        job = Job(interval, self)
        return job
    
    def run_pending(self) -> None:
        """Run all jobs that are scheduled to run."""
        runnable_jobs = [job for job in self.jobs if job.should_run()]
        for job in runnable_jobs:
            self._run_job(job)
    
    def run_all(self, delay_seconds: int = 0) -> None:
        """Run all jobs, regardless of schedule."""
        for job in self.jobs[:]:
            self._run_job(job)
            if delay_seconds > 0:
                time.sleep(delay_seconds)
    
    def _run_job(self, job: Job) -> None:
        """Run a job and reschedule it."""
        ret = job.run()
        
        if isinstance(ret, CancelJob) or ret is CancelJob:
            self.cancel_job(job)
            return
        
        if job.cancel_after is not None and datetime.datetime.now() >= job.cancel_after:
            self.cancel_job(job)
            return
        
        job.next_run = job._calculate_next_run()
    
    def cancel_job(self, job: Job) -> None:
        """Remove a job from the scheduler."""
        try:
            self.jobs.remove(job)
        except ValueError:
            pass
    
    def clear(self, tag: Optional[str] = None) -> None:
        """Remove all jobs from the scheduler, or jobs with a specific tag."""
        if tag is None:
            self.jobs.clear()
        else:
            self.jobs = [job for job in self.jobs if tag not in job.tags]
    
    def get_jobs(self, tag: Optional[str] = None) -> List[Job]:
        """Get all jobs, or jobs with a specific tag."""
        if tag is None:
            return self.jobs[:]
        return [job for job in self.jobs if tag in job.tags]
    
    @property
    def idle_seconds(self) -> Optional[float]:
        """Number of seconds until the next job is scheduled to run."""
        if not self.jobs:
            return None
        return max(0, (min(job.next_run for job in self.jobs) - datetime.datetime.now()).total_seconds())


# Default scheduler instance
default_scheduler = Scheduler()


def every(interval: int = 1) -> Job:
    """Create a new job with the given interval using the default scheduler."""
    return default_scheduler.every(interval)


def run_pending() -> None:
    """Run all pending jobs using the default scheduler."""
    default_scheduler.run_pending()


def run_all(delay_seconds: int = 0) -> None:
    """Run all jobs using the default scheduler."""
    default_scheduler.run_all(delay_seconds)


def clear(tag: Optional[str] = None) -> None:
    """Clear all jobs from the default scheduler."""
    default_scheduler.clear(tag)


def cancel_job(job: Job) -> None:
    """Cancel a job from the default scheduler."""
    default_scheduler.cancel_job(job)


def get_jobs(tag: Optional[str] = None) -> List[Job]:
    """Get all jobs from the default scheduler."""
    return default_scheduler.get_jobs(tag)


def idle_seconds() -> Optional[float]:
    """Get idle seconds from the default scheduler."""
    return default_scheduler.idle_seconds


__all__ = [
    'every',
    'run_pending',
    'run_all',
    'clear',
    'cancel_job',
    'get_jobs',
    'idle_seconds',
    'Job',
    'Scheduler',
    'CancelJob',
]