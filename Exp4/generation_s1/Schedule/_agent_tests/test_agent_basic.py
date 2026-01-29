import datetime
import types
import schedule


class FrozenClock:
    def __init__(self, dt: datetime.datetime):
        self.dt = dt

    def now(self):
        return self.dt

    def set(self, dt: datetime.datetime):
        self.dt = dt


def test_module_exports_and_default_scheduler_wrappers(monkeypatch):
    # Ensure a clean default scheduler between tests
    schedule.clear()

    assert hasattr(schedule, "every")
    assert hasattr(schedule, "Job")
    assert hasattr(schedule, "Scheduler")

    ran = []
    schedule.every(1).seconds.do(lambda: ran.append("x"))
    assert len(schedule.default_scheduler.jobs) == 1

    # run_all runs regardless of due-ness
    schedule.run_all()
    assert ran == ["x"]


def test_next_run_seconds_and_run_pending_runs_once(monkeypatch):
    schedule.clear()
    clock = FrozenClock(datetime.datetime(2020, 1, 1, 0, 0, 0))
    monkeypatch.setattr(schedule, "_now", clock.now)

    calls = []
    schedule.every(10).seconds.do(lambda: calls.append(clock.dt))

    job = schedule.default_scheduler.jobs[0]
    assert job.next_run == datetime.datetime(2020, 1, 1, 0, 0, 10)

    # Not due yet
    clock.set(datetime.datetime(2020, 1, 1, 0, 0, 9))
    schedule.run_pending()
    assert calls == []

    # Due now: runs once, reschedules once (even if we jump far ahead)
    clock.set(datetime.datetime(2020, 1, 1, 0, 1, 0))
    schedule.run_pending()
    assert len(calls) == 1
    assert job.last_run == datetime.datetime(2020, 1, 1, 0, 1, 0)
    # next_run is based on "now" at reschedule
    assert job.next_run == datetime.datetime(2020, 1, 1, 0, 1, 10)

    # Still overdue by multiple intervals, but run_pending runs at most once per call
    clock.set(datetime.datetime(2020, 1, 1, 0, 5, 0))
    schedule.run_pending()
    assert len(calls) == 2


def test_run_pending_orders_by_next_run(monkeypatch):
    schedule.clear()
    clock = FrozenClock(datetime.datetime(2020, 1, 1, 0, 0, 0))
    monkeypatch.setattr(schedule, "_now", clock.now)

    order = []

    schedule.every(10).seconds.do(lambda: order.append("late"))
    schedule.every(5).seconds.do(lambda: order.append("early"))

    clock.set(datetime.datetime(2020, 1, 1, 0, 0, 10))
    schedule.run_pending()
    # both are due; should run early (5s) before late (10s)
    assert order == ["early", "late"]


def test_day_at_parsing_and_rollover(monkeypatch):
    schedule.clear()
    clock = FrozenClock(datetime.datetime(2020, 1, 1, 10, 0, 0))
    monkeypatch.setattr(schedule, "_now", clock.now)

    schedule.every().day.at("10:30").do(lambda: None)
    job = schedule.default_scheduler.jobs[0]
    assert job.next_run == datetime.datetime(2020, 1, 1, 10, 30, 0)

    schedule.clear()
    clock.set(datetime.datetime(2020, 1, 1, 10, 31, 0))
    schedule.every().day.at("10:30:15").do(lambda: None)
    job = schedule.default_scheduler.jobs[0]
    assert job.next_run == datetime.datetime(2020, 1, 2, 10, 30, 15)


def test_weekday_next_run_and_at(monkeypatch):
    schedule.clear()
    # Wednesday
    clock = FrozenClock(datetime.datetime(2020, 1, 1, 9, 0, 0))
    monkeypatch.setattr(schedule, "_now", clock.now)

    schedule.every().monday.at("12:00").do(lambda: None)
    job = schedule.default_scheduler.jobs[0]
    # Next Monday is 2020-01-06
    assert job.next_run == datetime.datetime(2020, 1, 6, 12, 0, 0)

    # If it is Monday after the scheduled time, should go to next week.
    schedule.clear()
    clock.set(datetime.datetime(2020, 1, 6, 13, 0, 0))  # Monday
    schedule.every().monday.at("12:00").do(lambda: None)
    job = schedule.default_scheduler.jobs[0]
    assert job.next_run == datetime.datetime(2020, 1, 13, 12, 0, 0)


def test_tags_get_jobs_and_clear(monkeypatch):
    schedule.clear()
    clock = FrozenClock(datetime.datetime(2020, 1, 1, 0, 0, 0))
    monkeypatch.setattr(schedule, "_now", clock.now)

    j1 = schedule.every().hour.do(lambda: None).tag("a")
    j2 = schedule.every().hour.do(lambda: None).tag("b")
    assert set(schedule.get_jobs("a")) == {j1}
    assert set(schedule.get_jobs("b")) == {j2}

    schedule.clear("a")
    assert j1 not in schedule.get_jobs()
    assert j2 in schedule.get_jobs()


def test_canceljob_removes_job(monkeypatch):
    schedule.clear()
    clock = FrozenClock(datetime.datetime(2020, 1, 1, 0, 0, 0))
    monkeypatch.setattr(schedule, "_now", clock.now)

    def f():
        return schedule.CancelJob

    schedule.every().seconds.do(f)
    assert len(schedule.get_jobs()) == 1
    schedule.run_all()
    assert len(schedule.get_jobs()) == 0


def test_run_all_delay_calls_sleep(monkeypatch):
    schedule.clear()
    clock = FrozenClock(datetime.datetime(2020, 1, 1, 0, 0, 0))
    monkeypatch.setattr(schedule, "_now", clock.now)

    schedule.every().hour.do(lambda: "a")
    schedule.every().hour.do(lambda: "b")

    sleeps = {"n": 0, "args": []}

    def fake_sleep(x):
        sleeps["n"] += 1
        sleeps["args"].append(x)

    monkeypatch.setattr(schedule.time, "sleep", fake_sleep)

    res = schedule.run_all(delay_seconds=2)
    assert res == ["a", "b"]
    assert sleeps["n"] == 1
    assert sleeps["args"] == [2]


def test_invalid_at_raises(monkeypatch):
    schedule.clear()
    with __import__("pytest").raises(schedule.ScheduleValueError):
        schedule.every().seconds.at("10:30")

    with __import__("pytest").raises(schedule.ScheduleValueError):
        schedule.every().day.at("25:00")

    with __import__("pytest").raises(schedule.ScheduleValueError):
        schedule.every().week.at("10:00")