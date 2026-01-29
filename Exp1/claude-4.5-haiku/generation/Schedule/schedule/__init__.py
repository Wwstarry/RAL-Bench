import datetime
import time
import functools
from typing import Callable, Optional, List, Any


class Job:
    """A scheduled job that encapsulates a job function and its schedule."""
    
    def __init__(self, interval: int, scheduler: 'Scheduler' = None):
        self.interval = interval
        self.scheduler = scheduler
        self.job_func: Optional[Callable] = None
        self.unit: Optional[str] = None
        self.at_time: Optional[datetime.time] = None
        self.start_day: Optional[str] = None
        self.next_run: Optional[datetime.datetime] = None
        self.period: Optional[datetime.timedelta] = None
        self.tags: set = set()
        self.latest: Optional[datetime.datetime] = None
        
    def do(self, job_func: Callable, *args, **kwargs) -> 'Job':
        """Schedule the function to be called."""
        self.job_func = functools.partial(job_func, *args, **kwargs)
        self._schedule_next_run()
        if self.scheduler:
            self.scheduler.jobs.append(self)
        return self
    
    def _schedule_next_run(self) -> None:
        """Calculate the next run time for this job."""
        if self.unit == 'seconds':
            self.period = datetime.timedelta(seconds=self.interval)
            self.next_run = datetime.datetime.now() + self.period
        elif self.unit == 'minutes':
            self.period = datetime.timedelta(minutes=self.interval)
            self.next_run = datetime.datetime.now() + self.period
        elif self.unit == 'hours':
            self.period = datetime.timedelta(hours=self.interval)
            self.next_run = datetime.datetime.now() + self.period
        elif self.unit == 'days':
            self.period = datetime.timedelta(days=self.interval)
            if self.at_time:
                self.next_run = self._schedule_next_run_at_time()
            else:
                self.next_run = datetime.datetime.now() + self.period
        elif self.unit == 'weeks':
            self.period = datetime.timedelta(weeks=self.interval)
            self.next_run = datetime.datetime.now() + self.period
        elif self.unit in ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'):
            self._schedule_next_run_weekday()
        else:
            self.next_run = datetime.datetime.now()
    
    def _schedule_next_run_at_time(self) -> datetime.datetime:
        """Schedule next run at a specific time of day."""
        now = datetime.datetime.now()
        next_run = now.replace(hour=self.at_time.hour, minute=self.at_time.minute, second=0, microsecond=0)
        
        if next_run <= now:
            next_run += datetime.timedelta(days=self.interval)
        
        return next_run
    
    def _schedule_next_run_weekday(self) -> None:
        """Schedule next run for a specific weekday."""
        weekdays = {
            'monday': 0,
            'tuesday': 1,
            'wednesday': 2,
            'thursday': 3,
            'friday': 4,
            'saturday': 5,
            'sunday': 6,
        }
        
        target_weekday = weekdays[self.unit]
        now = datetime.datetime.now()
        current_weekday = now.weekday()
        days_ahead = target_weekday - current_weekday
        
        if days_ahead <= 0:
            days_ahead += 7
        
        next_run = now + datetime.timedelta(days=days_ahead)
        
        if self.at_time:
            next_run = next_run.replace(hour=self.at_time.hour, minute=self.at_time.minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += datetime.timedelta(days=7)
        else:
            next_run = next_run.replace(hour=now.hour, minute=now.minute, second=now.second, microsecond=0)
        
        self.next_run = next_run
        self.period = datetime.timedelta(weeks=1)
    
    def should_run(self) -> bool:
        """Check if this job should run now."""
        return datetime.datetime.now() >= self.next_run
    
    def run(self) -> Any:
        """Run the job function."""
        self.latest = datetime.datetime.now()
        ret = self.job_func()
        self._schedule_next_run()
        return ret
    
    @property
    def seconds(self) -> 'Job':
        """Schedule the job to run every n seconds."""
        self.unit = 'seconds'
        return self
    
    @property
    def minutes(self) -> 'Job':
        """Schedule the job to run every n minutes."""
        self.unit = 'minutes'
        return self
    
    @property
    def hours(self) -> 'Job':
        """Schedule the job to run every n hours."""
        self.unit = 'hours'
        return self
    
    @property
    def hour(self) -> 'Job':
        """Schedule the job to run every hour."""
        self.interval = 1
        self.unit = 'hours'
        return self
    
    @property
    def day(self) -> 'Job':
        """Schedule the job to run every day."""
        self.interval = 1
        self.unit = 'days'
        return self
    
    @property
    def days(self) -> 'Job':
        """Schedule the job to run every n days."""
        self.unit = 'days'
        return self
    
    @property
    def weeks(self) -> 'Job':
        """Schedule the job to run every n weeks."""
        self.unit = 'weeks'
        return self
    
    @property
    def monday(self) -> 'Job':
        """Schedule the job to run every Monday."""
        self.unit = 'monday'
        self.start_day = 'monday'
        return self
    
    @property
    def tuesday(self) -> 'Job':
        """Schedule the job to run every Tuesday."""
        self.unit = 'tuesday'
        self.start_day = 'tuesday'
        return self
    
    @property
    def wednesday(self) -> 'Job':
        """Schedule the job to run every Wednesday."""
        self.unit = 'wednesday'
        self.start_day = 'wednesday'
        return self
    
    @property
    def thursday(self) -> 'Job':
        """Schedule the job to run every Thursday."""
        self.unit = 'thursday'
        self.start_day = 'thursday'
        return self
    
    @property
    def friday(self) -> 'Job':
        """Schedule the job to run every Friday."""
        self.unit = 'friday'
        self.start_day = 'friday'
        return self
    
    @property
    def saturday(self) -> 'Job':
        """Schedule the job to run every Saturday."""
        self.unit = 'saturday'
        self.start_day = 'saturday'
        return self
    
    @property
    def sunday(self) -> 'Job':
        """Schedule the job to run every Sunday."""
        self.unit = 'sunday'
        self.start_day = 'sunday'
        return self
    
    def at(self, time_str: str) -> 'Job':
        """Schedule the job to run at a specific time of day."""
        parts = time_str.split(':')
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        self.at_time = datetime.time(hour, minute)
        
        if self.unit in ('days', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'):
            self._schedule_next_run()
        
        return self
    
    def tag(self, *tags) -> 'Job':
        """Add tags to the job."""
        for tag in tags:
            self.tags.add(tag)
        return self
    
    def __repr__(self) -> str:
        if self.job_func is None:
            job_func_name = None
        else:
            job_func_name = self.job_func.func.__name__
        return f'Every {self.interval} {self.unit} do {job_func_name}() (last run: {self.latest}, next run: {self.next_run})'


class Scheduler:
    """A scheduler for managing multiple jobs."""
    
    def __init__(self):
        self.jobs: List[Job] = []
    
    def every(self, interval: int = 1) -> Job:
        """Create a new job."""
        job = Job(interval, self)
        return job
    
    def run_pending(self) -> None:
        """Run all jobs that are scheduled to run."""
        for job in self.jobs:
            if job.should_run():
                job.run()
    
    def run_all(self, delay_seconds: int = 0) -> None:
        """Run all jobs regardless of schedule."""
        for job in self.jobs:
            job.run()
            if delay_seconds:
                time.sleep(delay_seconds)
    
    def get_jobs(self, tag: Optional[str] = None) -> List[Job]:
        """Get jobs, optionally filtered by tag."""
        if tag is None:
            return self.jobs
        return [job for job in self.jobs if tag in job.tags]
    
    def clear(self, tag: Optional[str] = None) -> None:
        """Clear jobs, optionally filtered by tag."""
        if tag is None:
            self.jobs.clear()
        else:
            self.jobs = [job for job in self.jobs if tag not in job.tags]
    
    def remove(self, job: Job) -> None:
        """Remove a specific job."""
        if job in self.jobs:
            self.jobs.remove(job)
    
    def idle_seconds(self) -> Optional[float]:
        """Get the number of seconds until the next job should run."""
        if not self.jobs:
            return None
        
        next_run_times = [job.next_run for job in self.jobs if job.next_run]
        if not next_run_times:
            return None
        
        nearest_next_run = min(next_run_times)
        idle_time = (nearest_next_run - datetime.datetime.now()).total_seconds()
        return max(0, idle_time)


# Default scheduler instance
_default_scheduler = Scheduler()


def every(interval: int = 1) -> Job:
    """Create a new job on the default scheduler."""
    return _default_scheduler.every(interval)


def run_pending() -> None:
    """Run all pending jobs on the default scheduler."""
    _default_scheduler.run_pending()


def run_all(delay_seconds: int = 0) -> None:
    """Run all jobs on the default scheduler."""
    _default_scheduler.run_all(delay_seconds)


def get_jobs(tag: Optional[str] = None) -> List[Job]:
    """Get jobs from the default scheduler."""
    return _default_scheduler.get_jobs(tag)


def clear(tag: Optional[str] = None) -> None:
    """Clear jobs from the default scheduler."""
    _default_scheduler.clear(tag)


def remove(job: Job) -> None:
    """Remove a job from the default scheduler."""
    _default_scheduler.remove(job)


def idle_seconds() -> Optional[float]:
    """Get idle seconds for the default scheduler."""
    return _default_scheduler.idle_seconds()


__all__ = [
    'Job',
    'Scheduler',
    'every',
    'run_pending',
    'run_all',
    'get_jobs',
    'clear',
    'remove',
    'idle_seconds',
]