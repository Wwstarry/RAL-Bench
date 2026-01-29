import datetime
import time
import functools
from typing import Callable, Optional, Union, List


class Job:
    """A job to be scheduled."""
    
    def __init__(self, interval: int = 1):
        self.interval = interval
        self.job_func: Optional[Callable] = None
        self.unit: Optional[str] = None
        self.at_time: Optional[datetime.time] = None
        self.last_run: Optional[datetime.datetime] = None
        self.next_run: Optional[datetime.datetime] = None
        self.period: Optional[datetime.timedelta] = None
        self.start_day: Optional[int] = None
        self.tags: set = set()
        
    def __repr__(self) -> str:
        return f"Job(interval={self.interval}, unit={self.unit}, at={self.at_time})"
    
    def at(self, time_str: str) -> 'Job':
        """Schedule the job every day at a specific time.
        
        Args:
            time_str: A string in the format HH:MM
            
        Returns:
            The job instance
        """
        if self.unit not in ['days', 'day']:
            raise ValueError("The 'at' method should only be used with daily jobs.")
        
        hour, minute = time_str.split(':')
        self.at_time = datetime.time(int(hour), int(minute))
        return self
    
    def do(self, job_func: Callable, *args, **kwargs) -> 'Job':
        """Specify the job function to be run.
        
        Args:
            job_func: The function to run
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The job instance
        """
        self.job_func = functools.partial(job_func, *args, **kwargs)
        try:
            functools.update_wrapper(self, job_func)
        except AttributeError:
            # job_func might not have __name__ etc.
            pass
        self._schedule_next_run()
        return self
    
    @property
    def should_run(self) -> bool:
        """Check if the job should run now.
        
        Returns:
            True if the job should run, False otherwise
        """
        return datetime.datetime.now() >= self.next_run
    
    def run(self) -> bool:
        """Run the job and schedule the next run.
        
        Returns:
            True if the job was run successfully, False otherwise
        """
        if self.job_func is None:
            return False
        
        try:
            self.job_func()
        except Exception:
            # Log the exception but don't break the scheduler
            import traceback
            traceback.print_exc()
            return False
        
        self.last_run = datetime.datetime.now()
        self._schedule_next_run()
        return True
    
    def _schedule_next_run(self) -> None:
        """Schedule the next run time for the job."""
        if self.unit is None:
            raise ValueError("Job unit not set")
        
        if self.last_run is None:
            # First run
            self.last_run = datetime.datetime.now()
        
        if self.unit == 'seconds':
            self.period = datetime.timedelta(seconds=self.interval)
            self.next_run = self.last_run + self.period
        
        elif self.unit == 'minutes':
            self.period = datetime.timedelta(minutes=self.interval)
            self.next_run = self.last_run + self.period
        
        elif self.unit == 'hours':
            self.period = datetime.timedelta(hours=self.interval)
            self.next_run = self.last_run + self.period
        
        elif self.unit in ['days', 'day']:
            self.period = datetime.timedelta(days=self.interval)
            self.next_run = self.last_run + self.period
            
            if self.at_time is not None:
                # Set the time for the next run
                self.next_run = self.next_run.replace(
                    hour=self.at_time.hour,
                    minute=self.at_time.minute,
                    second=0,
                    microsecond=0
                )
                
                # If the time has already passed today, schedule for tomorrow
                if self.next_run <= datetime.datetime.now():
                    self.next_run += datetime.timedelta(days=1)
        
        elif self.unit == 'weeks':
            self.period = datetime.timedelta(weeks=self.interval)
            self.next_run = self.last_run + self.period
            
            if self.start_day is not None:
                # Calculate days until the target weekday
                days_ahead = self.start_day - self.next_run.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                self.next_run += datetime.timedelta(days=days_ahead)
        
        elif self.unit in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            # Map weekday names to numbers (Monday=0, Sunday=6)
            weekday_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            target_weekday = weekday_map[self.unit]
            
            # Calculate days until the target weekday
            days_ahead = target_weekday - datetime.datetime.now().weekday()
            if days_ahead <= 0:
                days_ahead += 7
            
            self.next_run = datetime.datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + datetime.timedelta(days=days_ahead)
            
            if self.at_time is not None:
                self.next_run = self.next_run.replace(
                    hour=self.at_time.hour,
                    minute=self.at_time.minute
                )
    
    def tag(self, *tags: str) -> 'Job':
        """Tag the job with the given tags.
        
        Args:
            *tags: Tags to add to the job
            
        Returns:
            The job instance
        """
        self.tags.update(tags)
        return self


class Scheduler:
    """A job scheduler."""
    
    def __init__(self):
        self.jobs: List[Job] = []
    
    def every(self, interval: int = 1) -> Job:
        """Schedule a new job.
        
        Args:
            interval: The interval at which to run the job
            
        Returns:
            A new Job instance
        """
        job = Job(interval)
        self.jobs.append(job)
        return job
    
    def run_pending(self) -> None:
        """Run all jobs that are scheduled to run."""
        runnable_jobs = (job for job in self.jobs if job.should_run)
        for job in runnable_jobs:
            job.run()
    
    def run_all(self, delay_seconds: int = 0) -> None:
        """Run all jobs regardless of their schedule.
        
        Args:
            delay_seconds: Number of seconds to wait between each job execution
        """
        for job in self.jobs:
            job.run()
            if delay_seconds > 0:
                time.sleep(delay_seconds)
    
    def clear(self, tag: Optional[str] = None) -> None:
        """Clear scheduled jobs.
        
        Args:
            tag: If specified, only clear jobs with this tag
        """
        if tag is None:
            self.jobs.clear()
        else:
            self.jobs = [job for job in self.jobs if tag not in job.tags]
    
    def cancel_job(self, job: Job) -> None:
        """Cancel a specific job.
        
        Args:
            job: The job to cancel
        """
        if job in self.jobs:
            self.jobs.remove(job)
    
    @property
    def next_run(self) -> Optional[datetime.datetime]:
        """Get the datetime when the next job should run.
        
        Returns:
            The datetime of the next run, or None if no jobs are scheduled
        """
        if not self.jobs:
            return None
        return min(job.next_run for job in self.jobs if job.next_run is not None)
    
    @property
    def idle_seconds(self) -> Optional[float]:
        """Get the number of seconds until the next job should run.
        
        Returns:
            Number of seconds until next run, or None if no jobs are scheduled
        """
        if not self.jobs:
            return None
        
        next_run = self.next_run
        if next_run is None:
            return None
        
        return (next_run - datetime.datetime.now()).total_seconds()


# Create a default scheduler instance
default_scheduler = Scheduler()

# Expose the main API
every = default_scheduler.every
run_pending = default_scheduler.run_pending
run_all = default_scheduler.run_all
clear = default_scheduler.clear
cancel_job = default_scheduler.cancel_job
next_run = default_scheduler.next_run
idle_seconds = default_scheduler.idle_seconds

# Module-level exports
__all__ = [
    'every', 'run_pending', 'run_all', 'clear', 'cancel_job', 
    'next_run', 'idle_seconds', 'Job', 'Scheduler'
]