import datetime
import time
import threading
from typing import Optional, Callable, List, Set, Union
from enum import Enum


class TimeUnit(Enum):
    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"


class Job:
    """A periodic job as used by Scheduler."""
    
    def __init__(self, interval: int = 1):
        self.interval = interval
        self.unit: Optional[TimeUnit] = None
        self.at_time: Optional[str] = None
        self.start_day: Optional[int] = None  # 0-6 for Monday-Sunday
        self.job_func: Optional[Callable] = None
        self.last_run: Optional[datetime.datetime] = None
        self.next_run: Optional[datetime.datetime] = None
        self.tags: Set[str] = set()
        self.canceled = False
        
    def __repr__(self):
        return f"<Job {self.job_func.__name__ if self.job_func else 'None'}>"
    
    def _schedule_next_run(self):
        """Calculate the next run time based on the current configuration."""
        if self.unit is None:
            raise ValueError("Job unit not set")
        
        now = datetime.datetime.now()
        
        if self.unit == TimeUnit.SECONDS:
            self.next_run = now + datetime.timedelta(seconds=self.interval)
            
        elif self.unit == TimeUnit.MINUTES:
            self.next_run = now + datetime.timedelta(minutes=self.interval)
            
        elif self.unit == TimeUnit.HOURS:
            self.next_run = now + datetime.timedelta(hours=self.interval)
            
        elif self.unit == TimeUnit.DAYS:
            if self.at_time:
                # Parse HH:MM time
                hour, minute = map(int, self.at_time.split(':'))
                self.next_run = datetime.datetime.combine(
                    now.date(), datetime.time(hour, minute)
                )
                # If time already passed today, schedule for tomorrow
                if self.next_run <= now:
                    self.next_run += datetime.timedelta(days=self.interval)
            else:
                self.next_run = now + datetime.timedelta(days=self.interval)
                
        elif self.unit == TimeUnit.WEEKS:
            if self.start_day is not None:
                # Calculate days until next specified weekday
                days_ahead = (self.start_day - now.weekday()) % 7
                if days_ahead == 0:  # Today is the target day
                    days_ahead = 7
                next_day = now + datetime.timedelta(days=days_ahead)
                
                if self.at_time:
                    hour, minute = map(int, self.at_time.split(':'))
                    self.next_run = datetime.datetime.combine(
                        next_day.date(), datetime.time(hour, minute)
                    )
                else:
                    self.next_run = next_day.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                self.next_run = now + datetime.timedelta(weeks=self.interval)
    
    def seconds(self) -> 'Job':
        """Schedule job to run every n seconds."""
        self.unit = TimeUnit.SECONDS
        self._schedule_next_run()
        return self
    
    def minutes(self) -> 'Job':
        """Schedule job to run every n minutes."""
        self.unit = TimeUnit.MINUTES
        self._schedule_next_run()
        return self
    
    def hours(self) -> 'Job':
        """Schedule job to run every n hours."""
        self.unit = TimeUnit.HOURS
        self._schedule_next_run()
        return self
    
    def days(self) -> 'Job':
        """Schedule job to run every n days."""
        self.unit = TimeUnit.DAYS
        self._schedule_next_run()
        return self
    
    def weeks(self) -> 'Job':
        """Schedule job to run every n weeks."""
        self.unit = TimeUnit.WEEKS
        self._schedule_next_run()
        return self
    
    def at(self, time_str: str) -> 'Job':
        """Schedule job at specific time (for daily or weekly jobs)."""
        if self.unit not in [TimeUnit.DAYS, TimeUnit.WEEKS]:
            raise ValueError("at() is only supported for daily or weekly jobs")
        
        # Validate time format
        try:
            hour, minute = map(int, time_str.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid time format: {time_str}. Use HH:MM")
        
        self.at_time = time_str
        self._schedule_next_run()
        return self
    
    def do(self, job_func: Callable, *args, **kwargs) -> 'Job':
        """Specify the job function to run."""
        self.job_func = lambda: job_func(*args, **kwargs)
        return self
    
    def tag(self, *tags: str) -> 'Job':
        """Tag the job with given tags."""
        self.tags.update(tags)
        return self
    
    def run(self):
        """Run the job and immediately reschedule."""
        if self.job_func and not self.canceled:
            self.last_run = datetime.datetime.now()
            self.job_func()
            self._schedule_next_run()
    
    def should_run(self) -> bool:
        """Check if the job should run now."""
        if self.canceled:
            return False
        return datetime.datetime.now() >= self.next_run


class Scheduler:
    """Job scheduler that runs jobs at specified intervals."""
    
    def __init__(self):
        self.jobs: List[Job] = []
        self._stop_event = threading.Event()
        
    def every(self, interval: int = 1) -> Job:
        """Schedule a new periodic job."""
        job = Job(interval)
        self.jobs.append(job)
        return job
    
    def run_pending(self):
        """Run all jobs that are scheduled to run."""
        for job in self.jobs[:]:  # Copy list to allow removal during iteration
            if job.should_run():
                job.run()
    
    def run_all(self, delay_seconds: int = 0):
        """Run all jobs regardless of their schedule."""
        for job in self.jobs[:]:
            if not job.canceled:
                time.sleep(delay_seconds)
                job.run()
    
    def clear(self, tag: Optional[str] = None):
        """Clear scheduled jobs with given tag, or all jobs if tag is None."""
        if tag is None:
            self.jobs.clear()
        else:
            self.jobs = [job for job in self.jobs if tag not in job.tags]
    
    def cancel_job(self, job: Job):
        """Cancel a specific job."""
        job.canceled = True
        if job in self.jobs:
            self.jobs.remove(job)
    
    def next_run(self) -> Optional[datetime.datetime]:
        """Get datetime of next scheduled job run."""
        if not self.jobs:
            return None
        return min(job.next_run for job in self.jobs if job.next_run)
    
    def idle_seconds(self) -> Optional[float]:
        """Get number of seconds until next job."""
        next_run = self.next_run()
        if next_run is None:
            return None
        return (next_run - datetime.datetime.now()).total_seconds()


# Module-level default scheduler
_default_scheduler = Scheduler()


def every(interval: int = 1) -> Job:
    """Convenience function to schedule a job on the default scheduler."""
    return _default_scheduler.every(interval)


# Expose classes and functions at module level
__all__ = ['every', 'Job', 'Scheduler']

# Monkey-patch support for weekday methods
def _add_weekday_methods():
    """Add weekday methods to Job class (monday, tuesday, etc.)."""
    weekdays = [
        ('monday', 0),
        ('tuesday', 1),
        ('wednesday', 2),
        ('thursday', 3),
        ('friday', 4),
        ('saturday', 5),
        ('sunday', 6)
    ]
    
    for name, day_num in weekdays:
        def create_weekday_method(day_num):
            def method(self):
                self.unit = TimeUnit.WEEKS
                self.start_day = day_num
                self._schedule_next_run()
                return self
            return method
        
        setattr(Job, name, create_weekday_method(day_num))


_add_weekday_methods()

# Expose the default scheduler's methods at module level
def run_pending():
    _default_scheduler.run_pending()

def run_all(delay_seconds: int = 0):
    _default_scheduler.run_all(delay_seconds)

def clear(tag: Optional[str] = None):
    _default_scheduler.clear(tag)

def cancel_job(job: Job):
    _default_scheduler.cancel_job(job)

def next_run() -> Optional[datetime.datetime]:
    return _default_scheduler.next_run()

def idle_seconds() -> Optional[float]:
    return _default_scheduler.idle_seconds()

# Add these to __all__
__all__.extend([
    'run_pending', 'run_all', 'clear', 'cancel_job', 
    'next_run', 'idle_seconds'
])