import collections.abc
import datetime
import functools
import time

# --- Exceptions ---

class ScheduleError(Exception):
    """Base schedule exception"""
    pass

class ScheduleValueError(ValueError):
    """Passed an invalid value to a schedule function"""
    pass

class IntervalError(ScheduleValueError):
    """Raised when an invalid interval is used"""
    pass

# --- Sentinel ---

class _CancelJob:
    """
    A sentinel object to cancel a job.
    If a job function returns this object, the job is cancelled.
    """
    def __repr__(self):
        return 'CancelJob'

CancelJob = _CancelJob()

# --- Job Class ---

class Job:
    """
    A job definition.
    """
    def __init__(self, interval, scheduler):
        if not isinstance(interval, int) or interval <= 0:
            raise ScheduleValueError('interval must be a positive integer')
        self.interval = interval
        self.scheduler = scheduler
        self.unit = None
        self.at_time = None
        self.start_day = None
        self.job_func = None
        self.last_run = None
        self.next_run = None
        self.period = None
        self.tags = set()

    def __repr__(self):
        def format_time(t):
            return t.strftime('%Y-%m-%d %H:%M:%S') if t else '[never]'

        job_func_name = '[None]'
        args = '()'
        kwargs = '{}'
        if self.job_func:
            if hasattr(self.job_func, 'func'):
                job_func_name = self.job_func.func.__name__
                args = self.job_func.args
                kwargs = self.job_func.keywords
            else:
                job_func_name = self.job_func.__name__

        return (
            'Job(interval={}, unit={}, do={}, args={}, kwargs={}, '
            'last_run={}, next_run={})'.format(
                self.interval,
                self.unit,
                job_func_name,
                args,
                kwargs,
                format_time(self.last_run),
                format_time(self.next_run)
            )
        )

    # --- Time units ---

    @property
    def second(self):
        if self.interval != 1:
            raise IntervalError('Use every(1).second, not every(n).second')
        return self.seconds

    @property
    def seconds(self):
        self.unit = 'seconds'
        return self

    @property
    def minute(self):
        if self.interval != 1:
            raise IntervalError('Use every(1).minute, not every(n).minute')
        return self.minutes

    @property
    def minutes(self):
        self.unit = 'minutes'
        return self

    @property
    def hour(self):
        if self.interval != 1:
            raise IntervalError('Use every(1).hour, not every(n).hour')
        return self.hours

    @property
    def hours(self):
        self.unit = 'hours'
        return self

    @property
    def day(self):
        if self.interval != 1:
            raise IntervalError('Use every(1).day, not every(n).day')
        return self.days

    @property
    def days(self):
        self.unit = 'days'
        return self

    @property
    def week(self):
        if self.interval != 1:
            raise IntervalError('Use every(1).week, not every(n).week')
        return self.weeks

    @property
    def weeks(self):
        self.unit = 'weeks'
        return self

    # --- Weekday properties ---

    @property
    def monday(self):
        self.start_day = 'monday'
        return self.weeks

    @property
    def tuesday(self):
        self.start_day = 'tuesday'
        return self.weeks

    @property
    def wednesday(self):
        self.start_day = 'wednesday'
        return self.weeks

    @property
    def thursday(self):
        self.start_day = 'thursday'
        return self.weeks

    @property
    def friday(self):
        self.start_day = 'friday'
        return self.weeks

    @property
    def saturday(self):
        self.start_day = 'saturday'
        return self.weeks

    @property
    def sunday(self):
        self.start_day = 'sunday'
        return self.weeks

    # --- Job configuration ---

    def at(self, time_str):
        """
        Specify a particular time of day to run the job.
        e.g. .at("10:30") or .at("10:30:01")
        """
        if self.unit not in ('days', 'weeks'):
            raise ScheduleValueError('Invalid unit for .at(). Must be "days" or "weeks".')
        try:
            the_time = datetime.datetime.strptime(time_str, '%H:%M:%S').time()
        except ValueError:
            the_time = datetime.datetime.strptime(time_str, '%H:%M').time()
        self.at_time = the_time
        return self

    def do(self, job_func, *args, **kwargs):
        """
        Specifies the job_func that should be called every time the
        job runs.
        """
        self.job_func = functools.partial(job_func, *args, **kwargs)
        try:
            functools.update_wrapper(self.job_func, job_func)
        except AttributeError:
            pass  # job_func is not a function
        self._schedule_next_run()
        return self

    def tag(self, *tags):
        """
        Tags a job with one or more unique identifiers.
        """
        if not all(isinstance(tag, collections.abc.Hashable) for tag in tags):
            raise TypeError('Tags must be hashable')
        self.tags.update(tags)
        return self

    # --- Job execution ---

    @property
    def should_run(self):
        """
        :return: ``True`` if the job should be run now.
        """
        return datetime.datetime.now() >= self.next_run

    def run(self):
        """
        Run the job and immediately reschedule it.
        """
        ret = self.job_func()
        self.last_run = datetime.datetime.now()
        self._schedule_next_run()
        if ret is CancelJob:
            self.scheduler.cancel_job(self)
        return ret

    def _schedule_next_run(self):
        """
        Compute the instant when this job should run next.
        """
        if self.unit is None:
            raise ScheduleValueError("Job is not scheduled. Add a unit "
                                     "(.seconds, .minutes, etc.)")

        self.period = datetime.timedelta(**{self.unit: self.interval})
        now = datetime.datetime.now()

        if self.unit in ('seconds', 'minutes', 'hours'):
            self.next_run = now + self.period
            return

        if self.unit == 'days':
            if self.at_time is None:
                raise ScheduleValueError('.at() must be used with .day(s)')
            self.next_run = now.replace(
                hour=self.at_time.hour, minute=self.at_time.minute,
                second=self.at_time.second, microsecond=0)
            if self.next_run <= now:
                self.next_run += self.period
            return

        if self.unit == 'weeks':
            if self.start_day is None:
                raise ScheduleValueError('A weekday must be used with .week(s)')
            if self.at_time is None:
                raise ScheduleValueError('.at() must be used with .week(s)')

            weekdays = ('monday', 'tuesday', 'wednesday', 'thursday',
                        'friday', 'saturday', 'sunday')
            required_weekday = weekdays.index(self.start_day)

            self.next_run = now
            days_ahead = required_weekday - self.next_run.weekday()
            if days_ahead < 0:
                days_ahead += 7

            self.next_run += datetime.timedelta(days=days_ahead)
            self.next_run = self.next_run.replace(
                hour=self.at_time.hour, minute=self.at_time.minute,
                second=self.at_time.second, microsecond=0)

            if self.next_run <= now:
                self.next_run += self.period
            return

# --- Scheduler Class ---

class Scheduler:
    """
    Objects that hold a collection of jobs and schedule their execution.
    """
    def __init__(self):
        self.jobs = []

    def every(self, interval=1):
        """
        Schedule a new periodic job.
        """
        job = Job(interval, self)
        self.jobs.append(job)
        return job

    def run_pending(self):
        """
        Run all jobs that are scheduled to run.
        """
        runnable_jobs = sorted([job for job in self.jobs if job.should_run])
        for job in runnable_jobs:
            job.run()

    def run_all(self, delay_seconds=0):
        """
        Run all jobs regardless of their schedule.
        """
        for job in self.jobs[:]:
            job.run()
            time.sleep(delay_seconds)

    def clear(self, tag=None):
        """
        Deletes all jobs, or jobs with a specific tag.
        """
        if tag is None:
            self.jobs = []
        else:
            self.jobs = [job for job in self.jobs if tag not in job.tags]

    def cancel_job(self, job):
        """
        Delete a job from the scheduler.
        """
        try:
            self.jobs.remove(job)
        except ValueError:
            pass

    def get_jobs(self, tag=None):
        """
        Get all jobs, or jobs with a specific tag.
        """
        if tag is None:
            return self.jobs[:]
        return [job for job in self.jobs if tag in job.tags]

    @property
    def next_run(self):
        """
        Datetime of the next scheduled job to run.
        """
        if not self.jobs:
            return None
        runnable_jobs = [job for job in self.jobs if job.next_run]
        if not runnable_jobs:
            return None
        return min(job.next_run for job in runnable_jobs)

    @property
    def idle_seconds(self):
        """
        Number of seconds until the next job is scheduled to run.
        """
        next_run_time = self.next_run
        if not next_run_time:
            return None
        delta = next_run_time - datetime.datetime.now()
        return max(0, delta.total_seconds())

# --- Default Scheduler and API ---

default_scheduler = Scheduler()

every = default_scheduler.every
run_pending = default_scheduler.run_pending
run_all = default_scheduler.run_all
clear = default_scheduler.clear
cancel_job = default_scheduler.cancel_job
get_jobs = default_scheduler.get_jobs
idle_seconds = property(lambda: default_scheduler.idle_seconds)
next_run = property(lambda: default_scheduler.next_run)